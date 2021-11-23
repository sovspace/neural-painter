import logging
import io

from PIL import Image
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
import torchvision.transforms as transforms
import torchvision.models as models
from background_task import background

logger = logging.getLogger('django')


image_preproccessing_transform = transforms.Compose([
    transforms.Resize((128, 128)),
    transforms.ToTensor(),
])


def read_image(image_name):
    image = Image.open(image_name)
    image = image_preproccessing_transform(image)
    image = image[None, ...]
    return image


class ContentLoss(nn.Module):
    def __init__(self, target):
        super().__init__()
        self.target = target
        self.mse_criterion = nn.MSELoss()

    def forward(self, input):
        self.loss = self.mse_criterion(input, self.target)
        return input


def calculate_gram_matrix(input):
    batch_size, height_size, width_size, channel_size = input.size()
    features = input.view(batch_size * height_size, width_size * channel_size)
    gram_matrix = torch.mm(features, features.t())
    return gram_matrix.div(batch_size * height_size * width_size * channel_size)


class StyleLoss(nn.Module):
    def __init__(self, target_feature):
        super().__init__()
        self.target = calculate_gram_matrix(target_feature)
        self.mse_criterion = nn.MSELoss()

    def forward(self, input):
        gram_matrix = calculate_gram_matrix(input)
        self.loss = self.mse_criterion(gram_matrix, self.target)
        return input


class Normalization(nn.Module):
    def __init__(self, mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)):
        super().__init__()
        self.mean = torch.tensor(mean).view(-1, 1, 1)
        self.std = torch.tensor(std).view(-1, 1, 1)

    def forward(self, img):
        return (img - self.mean) / self.std


class StylizationModel(nn.Module):
    def __init__(self, content_image, style_image):
        super().__init__()

        content_layers = ['conv_4']
        style_layers = ['conv_1', 'conv_2', 'conv_3', 'conv_4', 'conv_5']

        self.content_losses = []
        self.style_losses = []

        pretrained_model = models.vgg19(pretrained=True).features.eval()

        self.model = nn.Sequential(Normalization())

        conv_index = 0

        for layer in pretrained_model.children():
            if isinstance(layer, nn.Conv2d):
                conv_index += 1
                name = f"conv_{conv_index}"
            elif isinstance(layer, nn.ReLU):
                name = f"relu_{conv_index}"
                layer = nn.ReLU(inplace=False)
            elif isinstance(layer, nn.MaxPool2d):
                name = f"pool_{conv_index}"
            elif isinstance(layer, nn.BatchNorm2d):
                name = f"bn_{conv_index}"
            else:
                raise RuntimeError('Unrecognized layer: {}'.format(layer.__class__.__name__))

            self.model.add_module(name, layer)

            if name in content_layers:
                target = self.model(content_image).detach()
                content_loss = ContentLoss(target)

                self.model.add_module(f"content_loss_{conv_index}", content_loss)
                self.content_losses.append(content_loss)

            if name in style_layers:
                target = self.model(style_image).detach()
                style_loss = StyleLoss(target)

                self.model.add_module(f"style_loss_{conv_index}", style_loss)
                self.style_losses.append(style_loss)

        for i in range(len(self.model) - 1, -1, -1):
            if isinstance(self.model[i], ContentLoss) or isinstance(self.model[i], StyleLoss):
                break

        self.model = self.model[:(i + 1)]

    def forward(self, generated_image):
        return self.model(generated_image)


def run_style_transfer(
        content_image,
        style_image,
        generated_image,
        steps_count=350,
        style_weight=1000000,
        content_weight=1
):
    model = StylizationModel(content_image, style_image)
    model.model.requires_grad_(False)

    optimizer = optim.LBFGS([generated_image])

    current_step = [0]
    while current_step[0] <= steps_count:
        def closure():
            with torch.no_grad():
                generated_image.clamp_(0, 1)

            optimizer.zero_grad()
            model(generated_image)

            style_loss = 0
            content_loss = 0

            for sl in model.style_losses:
                style_loss += sl.loss

            for cl in model.content_losses:
                content_loss += cl.loss

            style_loss *= style_weight
            content_loss *= content_weight
            loss = style_loss + content_loss
            loss.backward()

            current_step[0] += 1
            if current_step[0] % 50 == 0:
                logger.info(f"Step {current_step[0]}")

            return style_loss + content_loss

        optimizer.step(closure)

    with torch.no_grad():
        generated_image.clamp_(0, 1)

    return generated_image


@background(schedule=1)
def stylize_image(content_image_path, style_image_path, stylized_photo_pk):

    from NeuralPainter.models import StylizedPhoto

    content_image = read_image(content_image_path)
    style_image = read_image(style_image_path)
    generated_image = content_image.clone().requires_grad_(True)

    logger.info("Start running stylization")

    generated_image = run_style_transfer(content_image, style_image, generated_image)
    generated_image = generated_image[0].detach().cpu().numpy()
    generated_image = np.transpose(generated_image, (1, 2, 0))
    generated_image = (generated_image * 255).astype("uint8")
    generated_image = Image.fromarray(generated_image)

    generated_image_io = io.BytesIO()
    generated_image.save(generated_image_io, format="JPEG")
    StylizedPhoto.objects.get(pk=stylized_photo_pk).save_photo_stylization(generated_image_io)

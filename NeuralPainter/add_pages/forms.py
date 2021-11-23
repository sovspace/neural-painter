from django.core.exceptions import ValidationError
from django.forms import ModelForm, DateInput, TextInput
from django_select2.forms import ModelSelect2Widget

from NeuralPainter.models import Photo, StylizedPhoto, Painter, Paint, Genre


class StylizedPhotoForm(ModelForm):
    class Meta:
        model = StylizedPhoto
        fields = ('paint', 'based_photo')
        widgets = {
            'paint': ModelSelect2Widget(model=Paint, queryset=Paint.objects.filter(is_approved=True),
                                        search_fields=['name__contains'],),
            'based_photo': ModelSelect2Widget(model=Photo, search_fields=['name__contains']),
        }


class PainterForm(ModelForm):
    class Meta:
        model = Painter
        fields = ('name', 'photo', 'biography', 'genres', 'death_date', 'birth_date')

        widgets = {
            'name': TextInput(
                attrs={'placeholder': 'Enter name'}
            ),

            'genres': ModelSelect2Widget(model=Genre, queryset=Genre.objects.filter(is_approved=True),
                                         search_fields=['name__contains'], ),
            "death_date": DateInput(
                format='%m/%d/%Y',
                attrs={'class': 'form-control', 'placeholder': 'Select a date', 'type': 'date'}
            ),

            "birth_date": DateInput(
                format='%m/%d/%Y',
                attrs={'class': 'form-control', 'placeholder': 'Select a date', 'type': 'date'}
            ),
        }

        labels = {
            'name': 'Painter’s name',
            'death_date': 'Died',
            'birth_date': 'Born',
        }

    def clean(self):
        super().clean()
        death_date = self.cleaned_data.get('death_date')
        birth_date = self.cleaned_data.get('birth_date')
        if death_date < birth_date:
            raise ValidationError('Death date is bigger than birth date')


class PaintForm(ModelForm):
    class Meta:
        model = Paint
        fields = ('name', 'paint', 'painter', 'genre')
        widgets = {
            'painter': ModelSelect2Widget(model=Painter, queryset=Painter.objects.filter(is_approved=True),
                                          search_fields=['name__contains'],),
            'genre': ModelSelect2Widget(model=Genre, queryset=Genre.objects.filter(is_approved=True),
                                        search_fields=['name__contains'],),
        }



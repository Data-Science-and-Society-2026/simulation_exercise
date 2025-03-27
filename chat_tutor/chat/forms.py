from django import forms


class SetupForm(forms.Form):
    course_name = forms.CharField(max_length=100, label="Course Name")
    familiarity = forms.ChoiceField(
        choices=[("Beginner", "Beginner"), ("Intermediate", "Intermediate"), ("Advanced", "Advanced")]
    )
    student_name = forms.CharField(max_length=100, label="Your Name")

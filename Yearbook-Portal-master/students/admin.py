from django.contrib import admin
from students.models import Profile,Testimonial, ProfileQuestion, ProfileAnswers, PollQuestion, PollAnswer, Memories
# Register your models here.

admin.site.register(Profile)
admin.site.register(Testimonial)
admin.site.register(ProfileQuestion)
admin.site.register(ProfileAnswers)
admin.site.register(PollQuestion)
admin.site.register(PollAnswer)
admin.site.register(Memories)

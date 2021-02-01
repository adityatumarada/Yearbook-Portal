from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse, HttpResponseBadRequest
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Testimonial, PollAnswer, PollQuestion, ProfileAnswers, ProfileQuestion, Profile
from django.db.models.functions import Length, Lower
from PIL import Image, ImageOps
import os
import re
from yearbook.settings import BASE_DIR, MEDIA_ROOT, POLL_STOP, PORTAL_STOP, PRODUCTION

# Create your views here.

profile_pic_upload_folder = os.path.join(MEDIA_ROOT, Profile.profile_pic.field.upload_to)


def votes_sort_key(item):
    return len(item[1])


def nominees_sort_key(item):
    return item.full_name


@login_required
def home(request):
    if request.method == 'GET':
        if request.user and not request.user.is_anonymous:
            logged_in = True
        else:
            logged_in = False
        if logged_in:
            user = User.objects.filter(username=request.user.username).first()
            poll_questions = PollQuestion.objects.all().order_by("question")
            polls = {}
            if user.is_superuser:
                for question in poll_questions:
                    answers = PollAnswer.objects.filter(question=question)
                    answers_count = answers.count()
                    poll_dict = {}
                    for answer in answers:
                        if answer.answer in poll_dict.keys():
                            poll_dict[answer.answer].append(answer.voted_by)
                        else:
                            poll_dict[answer.answer] = [answer.voted_by]
                    polls[(question, answers_count)] = sorted(poll_dict.items(), key=votes_sort_key, reverse=True)
                context = {
                    'user': user,
                    'logged_in': logged_in
                }
                return render(request, 'admin_home.html', context)
            else:
                user_profile = Profile.objects.filter(user=user).first()
                if not user_profile.graduating:
                    context = {
                        'user': user,
                        'user_profile': user_profile,
                        'logged_in': logged_in
                    }
                    return render(request, 'polls.html', context)
                else:
                    testimonials = Testimonial.objects.filter(given_to=user_profile).order_by('-id')
                    #                    for question in poll_questions:
                    #                        answers = PollAnswer.objects.filter(question=question)
                    #                        myanswer = answers.filter(voted_by=user_profile).first()
                    #                        if myanswer:
                    #                            myanswer = myanswer.answer
                    #                        else:
                    #                            myanswer = None
                    #                        poll_nominees = []
                    #                        for answer in answers:
                    #                            if answer.answer not in poll_nominees:
                    #                                poll_nominees.append(answer.answer)
                    #                        polls[(question, myanswer)] = sorted(poll_nominees, key=nominees_sort_key)
                    context = {
                        'testimonials': testimonials,
                        'user': user,
                        'user_profile': user_profile,
                        'logged_in': logged_in
                    }
                    return render(request, 'home.html', context)
        else:
            return HttpResponseRedirect(reverse('login'))
    else:
        return error404(request)


@login_required
def profile(request, username):
    if request.method == 'GET':
        if request.user and not request.user.is_anonymous:
            user = User.objects.filter(username=request.user.username).first()
            user_profile = Profile.objects.filter(user=user).first()
            profile_user = User.objects.filter(username=username).first()
            if profile_user:
                if profile_user.is_superuser:
                    return error404(request)
                if profile_user == user:
                    myprofile = True
                else:
                    myprofile = False
                profile = Profile.objects.filter(user=profile_user).first()
                if not profile.graduating:
                    context = {
                        'logged_in': True,
                        'user': user,
                        'myprofile': myprofile,
                        'profile': profile
                    }
                    return render(request, 'profile.html', context)
                else:
                    testimonials = Testimonial.objects.filter(given_to=profile).order_by('-favourite',
                                                                                         Length('content').desc(),
                                                                                         '-id')
                    profile_questions = ProfileQuestion.objects.all()
                    profile_answers = ProfileAnswers.objects.filter(profile=profile)
                    mytestimonial = testimonials.filter(given_by=user_profile).first()
                    answers = {}
                    for question in profile_questions:
                        answers[question] = profile_answers.filter(question=question).first()
                    context = {
                        'logged_in': True,
                        'myprofile': myprofile,
                        'user': user,
                        'testimonials': testimonials,
                        'mytestimonial': mytestimonial,
                        'profile': profile,
                        'answers': answers
                    }
                    return render(request, 'profile.html', context)
            else:
                return error404(request)
        else:
            profile_user = User.objects.filter(username=username).first()
            if profile_user:
                if profile_user.is_superuser:
                    return error404(request)
                profile = Profile.objects.filter(user=profile_user).first()
                if not profile.graduating:
                    context = {
                        'logged_in': False,
                        'profile': profile
                    }
                    return render(request, 'profile.html', context)
                else:
                    testimonials = Testimonial.objects.filter(given_to=profile).order_by('-id')
                    profile_questions = ProfileQuestion.objects.all()
                    profile_answers = ProfileAnswers.objects.filter(profile=profile)
                    answers = {}
                    for question in profile_questions:
                        answers[question] = profile_answers.filter(question=question).first()
                    context = {
                        'logged_in': False,
                        'testimonials': testimonials,
                        'profile': profile,
                        'answers': answers
                    }
                    return render(request, 'profile.html', context)
            else:
                return error404(request)
    else:
        return error404(request)


@login_required
def search(request):
    if request.method == 'GET':
        if request.user and not request.user.is_anonymous:
            user = User.objects.filter(username=request.user.username).first()
            key = request.GET.get("key", "")
            json = request.GET.get("json", "")
            if key and key != "":
                profiles = Profile.objects.filter(user__first_name__contains=key.upper(), graduating=True)
            else:
                if json != "1":
                    return HttpResponseRedirect(reverse('home'))
                else:
                    return JsonResponse([], safe=False)
            profile_values = []
            page_profiles = profiles.exclude(user=user)
            more_profiles = False
            if page_profiles.count() > 20:
                more_profiles = True
            if json == "1":
                for profile in profiles[:10]:
                    profile_values.append({'username': profile.user.username, 'name': profile.full_name})
                return JsonResponse(profile_values, safe=False)
            else:
                context = {
                    'logged_in': True,
                    'user': user,
                    'profiles': page_profiles[:20],
                    'more_profiles': more_profiles
                }
                return render(request, 'search.html', context)
        else:
            key = request.GET.get("key", "")
            if key and key != "":
                profiles = Profile.objects.filter(user__first_name__contains=key.upper(), graduating=True)
            else:
                return HttpResponseRedirect(reverse('home'))
            more_profiles = False
            if profiles.count() > 20:
                more_profiles = True
            context = {
                'logged_in': False,
                'profiles': profiles[:20],
                'more_profiles': more_profiles
            }
            return render(request, 'search.html', context)
    else:
        return error404(request)


def login(request):
    if request.method == 'GET':
        if request.user and not request.user.is_anonymous:
            user = User.objects.filter(username=request.user.username).first()
            context = {
                'logged_in': True,
                'user': user,
                'production': PRODUCTION
            }
            return render(request, 'login.html', context)
        else:
            next = request.GET.get('next', "/yearbook")
            context = {
                'logged_in': False,
                'next': next,
                'production': PRODUCTION
            }
            return render(request, 'login.html', context)
    else:
        return error404(request)


@login_required
def edit_profile(request):
    if request.method == 'GET':
        user = User.objects.filter(username=request.user.username).first()
        profile = Profile.objects.filter(user=user).first()
        errors = [0, 0]
        if user.is_superuser:
            return error404(request)
        context = {
            'updated': False,
            'user': user,
            'profile': profile,
            'errors': errors,
            'logged_in': True
        }
        return render(request, 'editprofile.html', context)
    else:
        if not PORTAL_STOP:
            user = User.objects.filter(username=request.user.username).first()
            profile = Profile.objects.filter(user=user).first()
            new_name = request.POST.get("name", "")
            errors = [0, 0]
            if user.is_superuser:
                return error404(request)
            if len(new_name) < 50 and new_name != "":
                profile.full_name = new_name
            else:
                errors[0] = 1
            new_bio = request.POST.get("bio", "")
            if len(new_bio) <= 500:
                profile.bio = new_bio
            else:
                errors[1] = 1
            profile.save()
            context = {
                'updated': True,
                'profile': profile,
                'errors': errors,
                'logged_in': True
            }
            if errors[0] + errors[1] == 0:
                return render(request, 'editprofile.html', context)
            else:
                context['updated'] = False
                return render(request, 'editprofile.html', context)
        else:
            return JsonResponse({'status': 0, 'error': "Sorry, all changes to the portal have been stopped."})


@login_required
def upload_profile_pic(request):
    if request.method == 'POST':
        if not PORTAL_STOP:
            user = User.objects.filter(username=request.user.username).first()
            profile = Profile.objects.filter(user=user).first()
            try:
                x = request.POST.get("x", "")
                x = float(x)
            except:
                return JsonResponse({'status': 0,
                                     'error': "Wrong crop details\nPlease provide an image which is larger than 500x500\nUse JPEG or PNG format"})
            try:
                y = request.POST.get("y", "")
                y = float(y)
            except:
                return JsonResponse({'status': 0,
                                     'error': "Wrong crop details\nPlease provide an image which is larger than 500x500\nUse JPEG or PNG format"})
            try:
                height = request.POST.get("height", "")
                height = float(height)
            except:
                return JsonResponse({'status': 0,
                                     'error': "Wrong crop details\nPlease provide an image which is larger than 500x500\nUse JPEG or PNG format"})
            try:
                width = request.POST.get("width", "")
                width = float(width)
            except:
                return JsonResponse({'status': 0,
                                     'error': "Wrong crop details\nPlease provide an image which is larger than 500x500\nUse JPEG or PNG format"})
            if width < 490 or height < 490:
                return JsonResponse({'status': 0,
                                     'error': "Wrong image size\nPlease provide an image which is larger than 500x500\nUse JPEG or PNG format"})
            try:
                uploaded_pic = request.FILES["profile_pic"]
                image = Image.open(uploaded_pic)
                image = ImageOps.exif_transpose(image)
                cropped_image = image.crop((x, y, width + x, height + y))
                resized_image = cropped_image.resize((500, 500), Image.ANTIALIAS)
            except:
                return JsonResponse({'status': 0,
                                     'error': "Error processing image\nPlease provide an image which is larger than 500x500\nUse JPEG or PNG format"})
            extension = uploaded_pic.name.split('.')[-1]
            profile_pic_path = os.path.join(profile_pic_upload_folder, user.username + '.' + extension.lower())
            resized_image.save(profile_pic_path)
            profile.profile_pic = os.path.join(Profile.profile_pic.field.upload_to,
                                               user.username + '.' + extension.lower())
            profile.save()
            return JsonResponse({'status': 1, 'message': "Profile Pic Changed Successfully"})
        else:
            return JsonResponse({'status': 0, 'error': "Sorry, all changes to the portal have been stopped."})
    else:
        return error404(request)


@login_required
def add_testimonial(request, username):
    if request.method == 'GET':
        return error404(request)
    else:
        if not PORTAL_STOP:
            given_by = User.objects.filter(username=request.user.username).first()
            given_by_profile = Profile.objects.filter(user=given_by).first()
            given_to = User.objects.filter(username=username).first()
            if given_to:
                if given_to == given_by:
                    return JsonResponse({'status': 0, 'error': "You can't write a testimonial for yourself"})
                given_to_profile = Profile.objects.filter(user=given_to).first()
                if not given_to_profile.graduating:
                    return JsonResponse(
                        {'status': 0, 'error': "You can't write a testimonial for non-graduating batch"})
                content = request.POST.get("content", "")
                if len(content) <= 500 and content != "":
                    old_testimonial = Testimonial.objects.filter(given_to=given_to_profile,
                                                                 given_by=given_by_profile).first()
                    if old_testimonial:
                        old_testimonial.content = content
                        old_testimonial.save()
                        return JsonResponse({'status': 1, 'message': "edited"})
                    else:
                        Testimonial.objects.create(given_to=given_to_profile, given_by=given_by_profile,
                                                   content=content)
                        return JsonResponse({'status': 1, 'message': "added"})
                else:
                    return JsonResponse({'status': 0, 'error': "Testimonial size is " + str(
                        len(content)) + " characters, while maximum size allowed is 500 characters."})
            else:
                return JsonResponse({'status': 0, 'error': "User doesn't exist"})
        else:
            return JsonResponse({'status': 0, 'error': "Sorry, all changes to the portal have been stopped."})


@login_required
def delete_testimonial(request):
    if request.method == 'GET':
        return error404(request)
    else:
        if not PORTAL_STOP:
            user = User.objects.filter(username=request.user.username).first()
            testimonial_id = request.POST.get("testimonial_id", "-1")
            if not testimonial_id.isdecimal():
                return JsonResponse({'status': 0, 'error': "Testimonial doesn't exist"})
            testimonial = Testimonial.objects.filter(id=int(testimonial_id)).first()
            if testimonial:
                if user == testimonial.given_to.user or user == testimonial.given_by.user:
                    testimonial.delete()
                    return JsonResponse({'status': 1, 'message': "Testimonial deleted successfully"})
                else:
                    return JsonResponse({'status': 0, 'error': "You are not authorised to delete this"})
            else:
                return JsonResponse({'status': 0, 'error': "Testimonial doesn't exist"})
        else:
            return JsonResponse({'status': 0, 'error': "Sorry, all changes to the portal have been stopped."})


@login_required
def favourite_testimonial(request):
    if request.method == 'GET':
        return error404(request)
    else:
        if not PORTAL_STOP:
            user = User.objects.filter(username=request.user.username).first()
            user_profile = Profile.objects.filter(user=user).first()
            testimonial_id = request.POST.get("testimonial_id", "-1")
            if not testimonial_id.isdecimal():
                return JsonResponse({'status': 0, 'error': "Testimonial doesn't exist"})
            testimonial = Testimonial.objects.filter(id=int(testimonial_id)).first()
            if testimonial:
                if user == testimonial.given_to.user:
                    if testimonial.favourite:
                        testimonial.favourite = False
                        testimonial.save()
                        return JsonResponse({'status': 1, 'message': "Testimonial removed from favourites"})
                    else:
                        if Testimonial.objects.filter(given_to=user_profile, favourite=True).count() < 4:
                            testimonial.favourite = True
                            testimonial.save()
                            return JsonResponse({'status': 1, 'message': "Testimonial added to favourites"})
                        else:
                            return JsonResponse({'status': 0, 'error': "You can have only 4 favourite testimonials"})
                else:
                    return JsonResponse({'status': 0, 'error': "You are not authorised to favourite this testimonial"})
            else:
                return JsonResponse({'status': 0, 'error': "Testimonial doesn't exist"})
        else:
            return JsonResponse({'status': 0, 'error': "Sorry, all changes to the portal have been stopped."})


@login_required
def change_answer(request, username):
    if request.method == 'GET':
        return error404(request)
    else:
        if not PORTAL_STOP:
            user = User.objects.filter(username=request.user.username).first()
            profile_user = User.objects.filter(username=username).first()
            if user == profile_user:
                question_id = request.POST.get("question_id", "-1")
                profile = Profile.objects.filter(user=user).first()
                if not profile.graduating:
                    return JsonResponse({'status': 0, 'error': "Non-graduating batch can't answer profile questions"})
                if not question_id.isdecimal():
                    return JsonResponse({'status': 0, 'error': "Question doesn't exist"})
                new_answer = request.POST.get("answer", -1)
                if new_answer == -1:
                    return JsonResponse({'status': 0, 'error': "Answer size out of bounds"})
                if len(new_answer) <= 500:
                    question = ProfileQuestion.objects.filter(id=int(question_id)).first()
                    if question:
                        answer = ProfileAnswers.objects.filter(question=question, profile=profile).first()
                        if answer:
                            answer.answer = new_answer
                            answer.save()
                            return JsonResponse({'status': 1, 'message': "edited"})
                        else:
                            ProfileAnswers.objects.create(question=question, profile=profile, answer=new_answer)
                            return JsonResponse({'status': 1, 'message': "added"})
                    else:
                        return JsonResponse({'status': 0, 'error': "Question doesn't exist"})
                else:
                    return JsonResponse({'status': 0, 'error': "Answer size is " + str(
                        len(new_answer)) + " characters, while maximum size allowed is 500 characters."})
            else:
                return JsonResponse({'status': 0, 'error': "You are not authorised to change this"})
        else:
            return JsonResponse({'status': 0, 'error': "Sorry, all changes to the portal have been stopped."})


@login_required
def add_vote(request):
    if request.method == 'GET':
        return error404(request)
    else:
        if not POLL_STOP:
            user = User.objects.filter(username=request.user.username).first()
            user_profile = Profile.objects.filter(user=user).first()
            if not user_profile.graduating:
                return JsonResponse({'status': 0, 'error': "Non-graduating batch can't vote for polls"})
            vote_username = request.POST.get('voting_to', "")
            vote_user = User.objects.filter(username=vote_username).first()
            question_id = request.POST.get('question_id', "-1")
            origin = request.POST.get('origin', "polls")
            if not question_id.isdecimal():
                return JsonResponse({"status": 0, "error": "Poll doesn't exist"})
            poll_question = PollQuestion.objects.filter(id=int(question_id)).first()
            if not poll_question:
                return JsonResponse({"status": 0, "error": "Poll doesn't exist"})
            if not vote_user:
                return JsonResponse({"status": 0, "error": "Nominated user doesn't exist"})
            if origin != "home" and origin != "polls":
                origin = "polls"
            poll_answer = PollAnswer.objects.filter(voted_by=user_profile, question=poll_question).first()
            if poll_answer:
                poll_answer.answer = Profile.objects.filter(user=vote_user).first()
                poll_answer.save()
                return HttpResponseRedirect(reverse(origin))
            else:
                PollAnswer.objects.create(voted_by=user_profile, question=poll_question,
                                          answer=Profile.objects.filter(user=vote_user).first())
                return HttpResponseRedirect(reverse(origin))
        else:
            return JsonResponse({'status': 0, 'error': "Sorry, the polls have been freezed."})


def error404(request):
    if request.user and not request.user.is_anonymous:
        user = User.objects.filter(username=request.user.username).first()
        context = {
            'logged_in': True,
            'user': user
        }
        return render(request, '404.html', context)
    else:
        return render(request, '404.html')


@login_required
def polls(request):
    if request.method == 'GET':
        if request.user and not request.user.is_anonymous:
            logged_in = True
        else:
            logged_in = False
        if logged_in:
            user = User.objects.filter(username=request.user.username).first()
            poll_questions = PollQuestion.objects.all().order_by("question")
            polls = {}
            if user.is_superuser:
                for question in poll_questions:
                    answers = PollAnswer.objects.filter(question=question)
                    answers_count = answers.count()
                    poll_dict = {}
                    for answer in answers:
                        if answer.answer in poll_dict.keys():
                            poll_dict[answer.answer].append(answer.voted_by)
                        else:
                            poll_dict[answer.answer] = [answer.voted_by]
                    polls[(question, answers_count)] = sorted(poll_dict.items(), key=votes_sort_key, reverse=True)
                context = {
                    'polls': polls,
                    'user': user,
                    'logged_in': logged_in
                }
                return render(request, 'admin_home.html', context)
            else:
                user_profile = Profile.objects.filter(user=user).first()
                if not user_profile.graduating:
                    context = {
                        'user': user,
                        'user_profile': user_profile,
                        'logged_in': logged_in
                    }
                    return render(request, 'polls.html', context)
                else:
                    for question in poll_questions:
                        answers = PollAnswer.objects.filter(question=question)
                        myanswer = answers.filter(voted_by=user_profile).first()
                        if myanswer:
                            myanswer = myanswer.answer
                        else:
                            myanswer = None
                        poll_nominees = []
                        for answer in answers:
                            if answer.answer not in poll_nominees:
                                poll_nominees.append(answer.answer)
                        polls[(question, myanswer)] = sorted(poll_nominees, key=nominees_sort_key)
                    context = {
                        'polls': polls,
                        'user': user,
                        'user_profile': user_profile,
                        'logged_in': logged_in
                    }
                    return render(request, 'polls.html', context)
        else:
            return HttpResponseRedirect(reverse('login'))
    else:
        return error404(request)


@login_required
def write_testimonial(request):
    if request.method == 'GET':
        if request.user and not request.user.is_anonymous:
            logged_in = True
        else:
            logged_in = False
        if logged_in:
            user = User.objects.filter(username=request.user.username).first()
            profiles = Profile.objects.filter(graduating=True).order_by(Lower("full_name"))
            user_profile = Profile.objects.filter(user=user).first()
            testimonials = Testimonial.objects.filter(given_by=user_profile).order_by('-id')
            context = {
                'user': user,
                'profiles': profiles,
                'logged_in': logged_in,
                'testimonials': testimonials
            }
            return render(request, 'write_testimonial.html', context)
        else:
            return HttpResponseRedirect(reverse('login'))
    else:
        return error404(request)


def team(request):
    if request.method == 'GET':
        if request.user and not request.user.is_anonymous:
            logged_in = True
        else:
            logged_in = False
        if logged_in:
            user = User.objects.filter(username=request.user.username).first()
            context = {
                'user': user,
                'logged_in': logged_in
            }
            return render(request, 'team.html', context)
        else:
            context = {
                'logged_in': logged_in
            }
            return render(request, 'team.html', context)
    else:
        return error404(request)

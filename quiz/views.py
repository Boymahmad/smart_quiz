from django.http import JsonResponse
from .utils import get_next_difficulty
from django.contrib.auth.decorators import login_required
from .services.openai_service import analyze_student_level
from django.contrib import messages
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from .models import Subject, Question, Profile, Result
from datetime import datetime, timedelta
import random

# Django administration
# Username: Boymahmad
# Password: 1234@#qW

# python manage.py import_questions questions.csv

# from django.contrib.admin.models import LogEntry
#
# # 1 = ADD, # 2 = CHANGE, # 3 = DELETE
# LogEntry.objects.filter(action_flag=3).delete()

def signup(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            Profile.objects.get_or_create(user=user)
            return redirect('quiz:login')
    else:
        form = UserCreationForm()

    return render(request, 'quiz/signup.html', {
        'form': form
    })


@login_required
def subject_list(request):
    user = request.user

    # аввал ҳама message-ҳои қаблиро пок мекунем (АМН)
    storage = messages.get_messages(request)
    storage.used = True

    if user.is_superuser:
        subjects = Subject.objects.all()

        messages.success(
            request,
            f"Ба Шумо муваффақият, {user.username}!"
        )

    else:
        profile, _ = Profile.objects.get_or_create(user=user)
        subjects = profile.subjects.all()

        if subjects.exists():
            messages.success(
                request,
                f"Ба Шумо муваффақият {user.username}!"
            )
        else:
            messages.warning(
                request,
                f"{user.username} ба Шумо ҳанӯз ягон фан иҷозат дода нашудааст. "
                "Ба администратор муроҷиат кунед."
            )

    return render(request, 'quiz/subject_list.html', {
        'subjects': subjects
    })

@login_required
def start_quiz(request, subject_id):
    user = request.user
    subject = get_object_or_404(Subject, id=subject_id)

    if not user.is_superuser:
        profile, _ = Profile.objects.get_or_create(user=user)
        if subject not in profile.subjects.all():
            return HttpResponseForbidden(
                f"{user.username} Шумо ба ин фан иҷозат надоред"
            )

    # 🧹 тоза кардани ҳамаи session-и тест
    for key in list(request.session.keys()):
        if key.startswith('quiz_'):
            del request.session[key]

    # иҷозат диҳем натиҷа аз нав сабт шавад
    request.session.pop('quiz_result_saved', None)

    # маълумоти ибтидоӣ
    request.session['quiz_current_difficulty'] = 'easy'
    request.session['quiz_asked_questions'] = []
    request.session['quiz_questions_count'] = 0
    request.session['quiz_correct_answers'] = 0

    request.session['quiz_stats'] = {
        'easy': 0,
        'medium': 0,
        'hard': 0,
    }

    # вақт
    start_ts = int(datetime.now().timestamp())
    end_ts = int(
        (datetime.now() + timedelta(minutes=subject.timer_minutes)).timestamp()
    )

    request.session['quiz_start_ts'] = start_ts
    request.session['quiz_end_ts'] = end_ts

    # шумораи умумии саволҳо
    request.session['quiz_max_questions'] = Question.objects.filter(
        subject=subject
    ).count()

    return redirect('quiz:quiz_question', subject_id=subject.id)

@login_required
def quiz_question(request, subject_id):
    user = request.user
    subject = get_object_or_404(Subject, id=subject_id)

    if not user.is_superuser:
        profile, _ = Profile.objects.get_or_create(user=user)
        if subject not in profile.subjects.all():
            return HttpResponseForbidden("Шумо ба ин фан иҷозат надоред")

    end_ts = request.session.get('quiz_end_ts')
    if not end_ts or int(datetime.now().timestamp()) >= end_ts:
        return redirect('quiz:quiz_result', subject_id=subject.id)

    current_difficulty = request.session.get('quiz_current_difficulty', 'easy')
    asked_questions = request.session.get('quiz_asked_questions', [])
    questions_count = request.session.get('quiz_questions_count', 0)
    correct_answers = request.session.get('quiz_correct_answers', 0)
    max_questions = request.session.get('quiz_max_questions', 0)

    if questions_count >= max_questions:
        return redirect('quiz:quiz_result', subject_id=subject.id)

    feedback = None
    last_correct = None

    if request.method == 'POST':
        prev_id = request.session.get('quiz_current_question_id')
        selected = request.POST.get('option')

        if prev_id and selected:
            prev_q = get_object_or_404(Question, id=prev_id)
            is_correct = selected == prev_q.correct_option
            last_correct = is_correct

            stats = request.session.get('quiz_stats', {
                'easy': 0,
                'medium': 0,
                'hard': 0,
            })

            if is_correct:
                correct_answers += 1
                stats[prev_q.difficulty] += 1
                feedback = "Офарин! Ҷавоби дуруст ✅"
            else:
                feedback = "Ҷавоби нодуруст ❌"

            request.session['quiz_stats'] = stats

            current_difficulty = get_next_difficulty(
                current=current_difficulty,
                is_correct=is_correct
            )

            questions_count += 1
            request.session['quiz_questions_count'] = questions_count
            request.session['quiz_correct_answers'] = correct_answers
            request.session['quiz_current_difficulty'] = current_difficulty

            if questions_count >= max_questions:
                return redirect('quiz:quiz_result', subject_id=subject.id)

    available = Question.objects.filter(
        subject=subject,
        difficulty=current_difficulty
    ).exclude(id__in=asked_questions)

    if not available.exists():
        for level in ['hard', 'medium', 'easy']:
            fallback = Question.objects.filter(
                subject=subject,
                difficulty=level
            ).exclude(id__in=asked_questions)

            if fallback.exists():
                available = fallback
                current_difficulty = level
                request.session['quiz_current_difficulty'] = level
                break

    if not available.exists():
        return redirect('quiz:quiz_result', subject_id=subject.id)

    question = random.choice(list(available))
    asked_questions.append(question.id)

    request.session['quiz_asked_questions'] = asked_questions
    request.session['quiz_current_question_id'] = question.id

    return render(request, 'quiz/question.html', {
        'subject': subject,
        'question': question,
        'questions_count': questions_count + 1,
        'max_questions': max_questions,
        'end_ts': end_ts,
        'feedback': feedback,
        'last_correct': last_correct,
    })

@login_required
def quiz_result(request, subject_id):
    user = request.user
    subject = get_object_or_404(Subject, id=subject_id)

    if not user.is_superuser:
        profile, _ = Profile.objects.get_or_create(user=user)
        if subject not in profile.subjects.all():
            return HttpResponseForbidden(
                f"{user.username} Шумо ба ин фан иҷозат надоред"
            )

    correct_answers = request.session.get('quiz_correct_answers', 0)
    questions_count = request.session.get('quiz_questions_count', 0)
    percent = round((correct_answers / questions_count) * 100, 2) if questions_count else 0

    stats = request.session.get('quiz_stats', {
        'easy': 0,
        'medium': 0,
        'hard': 0,
    })

    start_ts = request.session.get('quiz_start_ts')
    end_ts = request.session.get('quiz_end_ts')
    now_ts = int(datetime.now().timestamp())

    used_minutes = 0
    used_seconds = 0

    if start_ts and end_ts:
        used = max(0, min(now_ts, end_ts) - start_ts)
        used_minutes = used // 60
        used_seconds = used % 60

    if not request.session.get('quiz_result_saved'):
        Result.objects.create(
            user=user,
            subject=subject,
            score=correct_answers,
            total_questions=questions_count
        )
        request.session['quiz_result_saved'] = True

    return render(request, 'quiz/result.html', {
        'subject': subject,
        'correct_answers': correct_answers,
        'questions_count': questions_count,
        'percent': percent,
        'easy_correct': stats.get('easy', 0),
        'medium_correct': stats.get('medium', 0),
        'hard_correct': stats.get('hard', 0),
        'used_minutes': used_minutes,
        'used_seconds': used_seconds,
        'total_minutes': subject.timer_minutes,
    })

@login_required
def student_level_json(request):
    try:
        easy = int(request.GET.get("easy", 0))
        medium = int(request.GET.get("medium", 0))
        hard = int(request.GET.get("hard", 0))

        correct = int(request.GET.get("correct", 0))
        total = int(request.GET.get("total", 0))
        percent = float(request.GET.get("score", 0))

        # гирифтани охирин натиҷаи тест
        result_obj = Result.objects.filter(
            user=request.user
        ).order_by("-created_at").first()

        subject_name = "Номаълум"
        if result_obj and result_obj.subject:
            subject_name = result_obj.subject.name

        ai_result = analyze_student_level(
            subject_name=subject_name,
            easy=easy,
            medium=medium,
            hard=hard,
            correct=correct,
            total=total,
            percent=percent
        )

        if ai_result.get("level") not in ["Хато", "AI ғайрифаъол аст"]:
            if result_obj:
                result_obj.level = ai_result.get("level")
                result_obj.description = ai_result.get("description")
                result_obj.recommendation = ai_result.get("recommendation")
                result_obj.save()

        return JsonResponse(ai_result)

    except Exception as e:
        print("AI ERROR:", e)

        return JsonResponse({
            "level": "",
            "description": "",
            "recommendation": ""
        })
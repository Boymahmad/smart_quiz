from django.contrib import admin, messages
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.urls import path
from django.shortcuts import render, redirect

from .models import Subject, Question, Profile, Result


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'timer_minutes')
    search_fields = ('name',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'subject', 'difficulty', 'correct_option')
    list_filter = ('subject', 'difficulty')
    search_fields = ('text',)


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    filter_horizontal = ('subjects',)


class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    change_list_template = "admin/user_changelist_with_assign.html"

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                "assign-subject/",
                self.admin_site.admin_view(self.assign_subject_view),
                name="assign-subject",
            ),
        ]
        return custom_urls + urls

    def assign_subject_view(self, request):
        if request.method == "POST":
            subject_id = request.POST.get("subject")
            user_ids = request.POST.getlist("user_ids")

            if not subject_id or not user_ids:
                messages.error(request, "Фан ё истифодабаранда интихоб нашудааст")
                return redirect("..")

            subject = Subject.objects.get(id=subject_id)

            for user in User.objects.filter(id__in=user_ids):
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.subjects.add(subject)

            messages.success(
                request,
                f"Фан «{subject.name}» ба {len(user_ids)} истифодабаранда дода шуд"
            )
            return redirect("..")

        users = User.objects.all()
        subjects = Subject.objects.all()

        return render(request, "admin/assign_subject_page.html", {
            "users": users,
            "subjects": subjects,
        })


admin.site.unregister(User)
admin.site.register(User, UserAdmin)


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'subject',
        'score',
        'percent_display',
        'ai_summary',
        'created_at',
    )

    list_filter = ('subject', 'created_at')
    search_fields = ('user__username',)

    readonly_fields = ('created_at', 'level', 'description', 'recommendation')

    # ===== ФОИЗ =====
    def percent_display(self, obj):
        if obj.total_questions:
            return f"{round((obj.score / obj.total_questions) * 100, 2)}%"
        return "0%"
    percent_display.short_description = "Фоиз (%)"

    # ===== AI SUMMARY (дар list) =====
    def ai_summary(self, obj):
        if obj.description:
            return obj.description[:60] + "..."
        return "—"
    ai_summary.short_description = "Тавсифи AI"

    # ===== FIELDSETS (танҳо агар AI бошад) =====
    def get_fieldsets(self, request, obj=None):
        base_fields = (
            'user',
            'subject',
            'score',
            'total_questions',
            'created_at',
        )

        # Ҳангоми ADD
        if not obj:
            return (
                (None, {'fields': base_fields}),
            )

        # Агар AI холӣ бошад → умуман нишон надеҳ
        if not obj.level and not obj.description and not obj.recommendation:
            return (
                (None, {'fields': base_fields}),
            )

        # Агар AI ҷавоб дошта бошад → нишон диҳ
        return (
            (None, {'fields': base_fields}),
            ('Таҳлили зеҳни сунъӣ (AI)', {
                'fields': ('level', 'description', 'recommendation'),
            }),
        )
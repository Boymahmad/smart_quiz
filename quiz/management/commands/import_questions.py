import csv
from django.core.management.base import BaseCommand
from django.db import transaction
from quiz.models import Subject, Question


class Command(BaseCommand):
    help = "Import questions from CSV file"

    def add_arguments(self, parser):
        parser.add_argument(
            'file_path',
            type=str,
            help='Path to CSV file'
        )

    @transaction.atomic
    def handle(self, *args, **options):
        file_path = options['file_path']
        created = 0

        with open(file_path, encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                # гирифтани вақт аз CSV
                subject_time = int(row.get('subject_time', 5))

                # fan (Subject) бо вақт
                subject, created_subject = Subject.objects.get_or_create(
                    name=row['subject'].strip(),
                    defaults={
                        'timer_minutes': subject_time
                    }
                )

                # агар фан аллакай вуҷуд дошт → вақтро нав мекунем
                if not created_subject and subject.timer_minutes != subject_time:
                    subject.timer_minutes = subject_time
                    subject.save()

                # савол (Question)
                question, is_created = Question.objects.get_or_create(
                    subject=subject,
                    text=row['question'].strip(),
                    defaults={
                        'difficulty': row['difficulty'],
                        'option_a': row['option_a'],
                        'option_b': row['option_b'],
                        'option_c': row.get('option_c', ''),
                        'option_d': row.get('option_d', ''),
                        'correct_option': row['correct_option'],
                    }
                )

                if is_created:
                    created += 1

        self.stdout.write(
            self.style.SUCCESS(f"Imported {created} questions successfully")
        )
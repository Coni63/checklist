from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import TaskComment, ProjectTask
from django.template.loader import render_to_string


class TaskCommentListView(LoginRequiredMixin, ListView):
    model = TaskComment
    template_name = "projects/partials/comment_list.html"
    context_object_name = "comments"

    def get_queryset(self):
        task_id = self.kwargs.get("task_id")
        result = TaskComment.objects.filter(
            project_task_id=task_id,
            deleted_at__isnull=True,
            parent_comment__isnull=True,  # Only top-level comments
        ).select_related("user", "project_task")
        return result

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task_id"] = self.kwargs.get("task_id")
        context["task"] = get_object_or_404(ProjectTask, id=self.kwargs.get("task_id"))
        return context


class TaskCommentCreateView(LoginRequiredMixin, CreateView):
    model = TaskComment
    fields = ["comment_text"]
    template_name = "projects/partials/comment_form.html"

    def form_valid(self, form):
        form.instance.user = self.request.user
        form.instance.project_task_id = self.kwargs.get("task_id")
        self.object = form.save()

        html = render_to_string(
            "projects/partials/comment_item.html",
            {
                "comment": self.object,
                "user": self.request.user,
            },
        )
        return HttpResponse(html)


class TaskCommentUpdateView(LoginRequiredMixin, UpdateView):
    # TODO: adjust & test when developped
    model = TaskComment
    fields = ["comment_text"]
    pk_url_kwarg = "comment_id"
    template_name = "projects/partials/comment_form.html"

    def get_queryset(self):
        # Only allow editing own comments
        return TaskComment.objects.filter(
            user=self.request.user, deleted_at__isnull=True
        )

    def form_valid(self, form):
        self.object = form.save()

        html = render_to_string(
            "projects/partials/comment_item.html",
            {
                "comment": self.object,
                "user": self.request.user,
            },
        )
        return HttpResponse(html)


class TaskCommentDeleteView(LoginRequiredMixin, DeleteView):
    model = TaskComment
    pk_url_kwarg = "comment_id"

    def get_queryset(self):
        # Only allow deleting own comments
        return TaskComment.objects.filter(
            user=self.request.user, deleted_at__isnull=True
        )

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.soft_delete()
        return HttpResponse("")  # Return empty response to remove the element

from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from .models import TaskComment, ProjectTask


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

        # Return only the updated comment list
        comments = TaskComment.objects.filter(
            project_task_id=self.kwargs.get("task_id"),
            deleted_at__isnull=True,
            parent_comment__isnull=True,
        ).select_related("user")

        from django.template.loader import render_to_string

        html = render_to_string(
            "projects/partials/comment_list_only.html",
            {
                "comments": comments,
                "task_id": self.kwargs.get("task_id"),
                "user": self.request.user,
            },
        )
        return HttpResponse(html)


class TaskCommentUpdateView(LoginRequiredMixin, UpdateView):
    model = TaskComment
    fields = ["comment_text"]
    template_name = "projects/partials/comment_edit_form.html"
    pk_url_kwarg = "comment_id"

    def get_queryset(self):
        # Only allow editing own comments
        return TaskComment.objects.filter(
            user=self.request.user, deleted_at__isnull=True
        )

    def form_valid(self, form):
        self.object = form.save()

        # Return the updated comment item
        from django.template.loader import render_to_string

        html = render_to_string(
            "projects/partials/comment_item.html",
            {"comment": self.object, "user": self.request.user},
        )
        return HttpResponse(html)

    def get(self, request, *args, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        from django.template.loader import render_to_string

        html = render_to_string(self.template_name, context)
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

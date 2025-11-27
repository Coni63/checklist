from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.contrib import messages

from templates_management.models import StepTemplate
from .models import Project, ProjectStep, ProjectTask
from .forms import ProjectCreationForm, ProjectSetupForm, QuickAddStepForm, ProjectSetupFormV2
from core.mixins import UserOwnedMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Max

class ProjectListView(UserOwnedMixin, ListView):
    model = Project
    template_name = 'projects/project_list.html'
    context_object_name = 'projects'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

class ProjectCreateView(LoginRequiredMixin, CreateView):
    model = Project
    form_class = ProjectCreationForm
    template_name = 'projects/project_create.html'
    
    def get_success_url(self):
        return reverse_lazy('projects:project_setup', kwargs={'pk': self.object.pk})
    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, f'Project "{form.instance.name}" created successfully!')
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, 'Please correct the errors below.')
        return super().form_invalid(form)

class ProjectSetupViewV2(LoginRequiredMixin, UpdateView):
    model = Project
    template_name = 'projects/project_setup_V2.html'
    fields = []  # We don't need form fields since we're handling it manually
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get all available step templates
        context['available_templates'] = StepTemplate.objects.filter(is_active=True).order_by('default_order')
        
        # Get current project steps
        context['project_steps'] = ProjectStep.objects.filter(
            project=self.object
        ).select_related('step_template').prefetch_related('tasks').order_by('order')
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle AJAX requests to add steps"""
        self.object = self.get_object()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return self.handle_ajax_request(request)
        
        # Regular form submission (if needed for other actions)
        return super().post(request, *args, **kwargs)
    
    def handle_ajax_request(self, request):
        """Handle AJAX requests for adding/removing steps"""
        action = request.POST.get('action')
        
        if action == 'add_step':
            return self.add_step(request)
        elif action == 'remove_step':
            return self.remove_step(request)
        
        return JsonResponse({'success': False, 'error': 'Invalid action'}, status=400)
    
    def add_step(self, request):
        """Add a new step to the project"""
        try:
            step_template_id = request.POST.get('step_template_id')
            override_name = request.POST.get('override_name', '').strip()
            
            step_template = get_object_or_404(StepTemplate, id=step_template_id, is_active=True)
            
            # Determine step order
            current_max_order = ProjectStep.objects.filter(
                project=self.object
            ).aggregate(Max('order'))['order__max'] or 0
            
            # Use override name or default template name
            step_title = override_name if override_name else step_template.title
            
            # Create the project step
            project_step = ProjectStep.objects.create(
                project=self.object,
                step_template=step_template,
                title=step_title,
                icon=getattr(step_template, 'icon', '📋'),
                order=current_max_order + 1
            )
            
            # Create tasks from template
            task_templates = step_template.tasks.filter(is_active=True).order_by('order')
            for j, task_template in enumerate(task_templates, start=1):
                ProjectTask.objects.create(
                    project_step=project_step,
                    task_template=task_template,
                    title=task_template.title,
                    info_url=getattr(task_template, 'info_url', ''),
                    order=j
                )
            
            # Return the newly created step data
            return JsonResponse({
                'success': True,
                'step': {
                    'id': project_step.id,
                    'title': project_step.title,
                    'icon': project_step.icon,
                    'task_count': task_templates.count()
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def remove_step(self, request):
        """Remove a step from the project"""
        try:
            step_id = request.POST.get('step_id')
            project_step = get_object_or_404(
                ProjectStep, 
                id=step_id, 
                project=self.object
            )
            
            project_step.delete()
            
            return JsonResponse({'success': True})
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)
    
    def get_success_url(self):
        """Redirect back to setup page"""
        return reverse_lazy('projects:project_setup_v2', kwargs={'pk': self.object.pk})


class ProjectSetupViewV1(LoginRequiredMixin, UpdateView):
    model = Project
    template_name = 'projects/project_setup.html'
    form_class = ProjectSetupForm
    
    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     kwargs['project'] = self.object
    #     print("get_form_kwargs", kwargs)
    #     return kwargs
    
    def get_context_data(self, **kwargs):
        # This return the project + internal variables like csrf token
        context = super().get_context_data(**kwargs)  

        print("ctx before", context)

        form = self.get_form()
        
        context['available_templates'] = form.get_available_templates()
        context['project_steps'] = form.get_project_steps()
        context['quick_add_form'] = QuickAddStepForm(project=self.object)
        
        print("ctx after", context)

        return context
    
    def form_valid(self, form):
        """Handle form submission and save project configuration"""
        try:
            # Save the project configuration
            project = form.save()
            messages.success(self.request, f'Project "{project.name}" configuration saved successfully!')
            return super().form_valid(form)
        except Exception as e:
            messages.error(self.request, f'Error saving project configuration: {str(e)}')
            return self.form_invalid(form)
    
    def get_success_url(self):
        """Redirect to project setup page after successful save"""
        return reverse_lazy('projects:project_setup', kwargs={'pk': self.object.pk})

class ProjectDetailView(UserOwnedMixin, DetailView):
    model = Project
    template_name = 'projects/project_detail.html'
    context_object_name = 'project'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['steps'] = self.object.steps.prefetch_related('tasks')
        context['completion'] = self.object.get_completion_percentage()
        return context

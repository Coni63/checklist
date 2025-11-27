# apps/projects/forms.py

from django import forms
from django.core.exceptions import ValidationError
from django.db import models
from .models import Project, ProjectStep, ProjectTask
from templates_management.models import StepTemplate


class ProjectCreationForm(forms.ModelForm):
    """Form for creating and editing projects"""
    
    class Meta:
        model = Project
        fields = ['name', 'description', 'status']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter project name (e.g., Dinner Party)',
                'autofocus': True,
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Optional: Describe your project...',
                'rows': 4,
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        labels = {
            'name': 'Project Name',
            'description': 'Description',
            'status': 'Status',
        }
        help_texts = {
            'name': 'Give your project a clear, descriptive name',
            'description': 'Add any notes or context about this project',
            'status': 'Set the current status of your project',
        }
    
    def clean_name(self):
        """Validate project name"""
        name = self.cleaned_data.get('name').strip()
        
        if not name:
            raise ValidationError('Project name is required')
        
        if len(name) < 3:
            raise ValidationError('Project name must be at least 3 characters')
        
        # Check for duplicate names (case-insensitive)
        if not self.instance.pk:
            duplicated_name = Project.objects.filter(
                name__iexact=name
            )
            if duplicated_name.exists():
                raise ValidationError('Project name already used')
        
        return name

class ProjectStepForm(forms.ModelForm):
    """Form for adding/editing a project step"""
    
    step_template = forms.ModelChoiceField(
        queryset=StepTemplate.objects.filter(is_active=True),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Step Template',
        help_text='Select a template or leave empty for custom step'
    )
    
    class Meta:
        model = ProjectStep
        fields = ['step_template', 'title', 'icon', 'order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter custom step name',
            }),
            'icon': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': '🎯 (emoji)',
                'maxlength': 10,
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
            }),
        }
        labels = {
            'title': 'Step Title',
            'icon': 'Icon',
            'order': 'Order',
        }
        help_texts = {
            'title': 'Custom name for this step (overrides template name)',
            'icon': 'Emoji to represent this step',
            'order': 'Position in the project (1 = first)',
        }
    
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # If editing, prefill template if available
        if self.instance.pk and self.instance.step_template:
            self.fields['step_template'].initial = self.instance.step_template
    
    def clean(self):
        cleaned_data = super().clean()
        step_template = cleaned_data.get('step_template')
        title = cleaned_data.get('title')
        icon = cleaned_data.get('icon')
        
        # If template is selected, use template values as defaults
        if step_template:
            if not title:
                cleaned_data['title'] = step_template.name
            if not icon:
                cleaned_data['icon'] = step_template.icon
        else:
            # Custom step requires title and icon
            if not title:
                raise ValidationError('Title is required for custom steps')
            if not icon:
                raise ValidationError('Icon is required for custom steps')
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set project if provided
        if self.instance:
            instance.project = self.instance
        
        if commit:
            instance.save()
        
        return instance


class BulkAddStepsForm(forms.Form):
    """Form for adding multiple step instances at once"""
    
    step_templates = forms.ModelMultipleChoiceField(
        queryset=StepTemplate.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'checkbox-list',
        }),
        label='Select Steps to Add',
        help_text='Choose one or more step templates to add to your project'
    )
    
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
        
        # Order templates by default_order
        self.fields['step_templates'].queryset = (
            StepTemplate.objects.filter(is_active=True)
            .order_by('default_order')
        )


class ProjectStepRenameForm(forms.Form):
    """Simple form for renaming a project step"""
    
    title = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Enter new step name',
        }),
        label='Step Name'
    )
    
    def __init__(self, *args, **kwargs):
        self.step = kwargs.pop('step', None)
        super().__init__(*args, **kwargs)
        
        if self.step:
            self.fields['title'].initial = self.step.title


class ProjectStepReorderForm(forms.Form):
    """Form for reordering steps via drag-and-drop"""
    
    step_order = forms.CharField(
        widget=forms.HiddenInput(),
        help_text='JSON array of step IDs in desired order'
    )
    
    def clean_step_order(self):
        """Validate and parse the step order JSON"""
        import json
        
        order_data = self.cleaned_data.get('step_order')
        
        try:
            step_ids = json.loads(order_data)
        except (json.JSONDecodeError, TypeError):
            raise ValidationError('Invalid order data')
        
        if not isinstance(step_ids, list):
            raise ValidationError('Order data must be a list')
        
        if not all(isinstance(id, int) for id in step_ids):
            raise ValidationError('All step IDs must be integers')
        
        return step_ids


class ProjectTaskForm(forms.ModelForm):
    """Form for adding/editing individual tasks"""
    
    class Meta:
        model = ProjectTask
        fields = ['title', 'info_url', 'order']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Enter task description',
            }),
            'info_url': forms.URLInput(attrs={
                'class': 'form-input',
                'placeholder': 'https://example.com/help',
            }),
            'order': forms.NumberInput(attrs={
                'class': 'form-input',
                'min': 1,
            }),
        }
        labels = {
            'title': 'Task Description',
            'info_url': 'Info/Documentation URL',
            'order': 'Order',
        }
        help_texts = {
            'title': 'What needs to be done?',
            'info_url': 'Optional link to instructions or documentation',
            'order': 'Position within this step',
        }
    
    def __init__(self, *args, **kwargs):
        self.instance_step = kwargs.pop('project_step', None)
        super().__init__(*args, **kwargs)
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        if self.instance_step:
            instance.project_step = self.instance_step
        
        if commit:
            instance.save()
        
        return instance


class ProjectTaskCommentForm(forms.ModelForm):
    """Form for updating task comments (simple version)"""
    
    class Meta:
        model = ProjectTask
        fields = ['comment']
        widgets = {
            'comment': forms.Textarea(attrs={
                'class': 'form-textarea',
                'placeholder': 'Add notes or comments about this task...',
                'rows': 3,
            }),
        }
        labels = {
            'comment': 'Task Notes',
        }


class ProjectSearchForm(forms.Form):
    """Form for searching and filtering projects"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Search projects...',
        }),
        label='Search'
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Status')] + Project.STATUS_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Status'
    )
    
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Default'),
            ('-created_at', 'Newest First'),
            ('created_at', 'Oldest First'),
            ('name', 'Name A-Z'),
            ('-name', 'Name Z-A'),
            ('-updated_at', 'Recently Updated'),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Sort By'
    )


# ============================================
# ProjectSetupForm - Main configuration form
# ============================================
class ProjectSetupFormV2(forms.Form):
    step_template = forms.ModelChoiceField(
        queryset=StepTemplate.objects.filter(is_active=True),
        required=True,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label='Step Template',
        help_text='Select a template or leave empty for custom step'
    )
    override_name = forms.CharField()

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance # instance should be Project in UpdateView context

    def save(self):        
        # Determine step order
        current_max_order = ProjectStep.objects.filter(project=self.instance).aggregate(models.Max('order'))['order__max'] or 0
        
        # Create the project step
        project_step = ProjectStep.objects.create(
            project=self.instance,
            step_template=self.step_template,
            title=self.override_name,
            icon=getattr(self.step_template, 'icon', '?'), # Safely access icon if it exists
            order=current_max_order + 1
        )
        
        # Create tasks from template
        # Assuming 'tasks' is the related_name from StepTemplate to TaskTemplate
        task_templates = self.step_template.tasks.filter(is_active=True).order_by('order') 
        for j, task_template in enumerate(task_templates, start=1):
            ProjectTask.objects.create(
                project_step=project_step,
                task_template=task_template,
                title=task_template.title,
                info_url=getattr(task_template, 'info_url', ''), # Safely access info_url
                order=j
            )
    


class ProjectSetupForm(forms.Form):
    """
    Main form for project setup page.
    Handles the overall project configuration state.
    """
    
    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance # instance should be Project in UpdateView context
            
        super().__init__(*args, **kwargs)

        # 1. Dynamically add fields for all available templates
        self.available_templates = self.get_available_templates()
        
        for template in self.available_templates:
            field_prefix = f'template_{template.id}'
            
            # --- Quantity Field ---
            # Set the initial value based on existing project steps, 
            # or default to 1 (as in your HTML) only if a new form, 
            # otherwise 0 is safer if you want a blank state.
            # However, for setup, we must check if any steps are linked to this template.
            # In your current logic, you're only CREATING steps, not updating/reloading existing ones.
            # For simplicity, we will stick to your HTML's default of '1' for now, 
            # but if you need to load existing counts, you'd calculate:
            # initial_quantity = ProjectStep.objects.filter(project=self.instance, step_template=template).count()
            
            # Since your HTML sets '1' as selected, we'll follow that initial logic for GET requests.
            # The 'selected' attribute in HTML is what the browser sends on an initial POST if not changed.
            
            self.fields[f'{field_prefix}_quantity'] = forms.IntegerField(
                widget=forms.TextInput(attrs={'min':0,'max': '10','type': 'number','value': 1})
            )

            # --- Names Field ---
            # We don't need to load initial names because you are only supporting "add new steps" on form submission.
            self.fields[f'{field_prefix}_names'] = forms.CharField(
                max_length=1000,
                required=False,
                widget=forms.Textarea(attrs={
                    'rows': 3,
                    'placeholder': "Leave empty to use template name\nOr enter custom names, one per instance"
                })
            )
            
            # Store the template instance on the form for easy access in the save method
            self.fields[f'{field_prefix}_quantity'].template = template
            

    # Your existing helper methods
    def get_available_templates(self):
        return StepTemplate.objects.filter(is_active=True).order_by('default_order')
    
    def get_project_steps(self):
        if self.instance:
            # Use 'steps' reverse relation assuming it's correctly set up in Project model
            return self.instance.steps.all()
            # Changed 'steps' to 'projectstep_set' for standard reverse relation name, 
            # update if you used a custom related_name
        return ProjectStep.objects.none()
        
    def get_template_preview(self, template_id):
        # ... (keep as is)
        pass

    def save(self, commit=True):
        if not self.instance:
            raise ValueError("Project is required to save configuration")
        
        # --- The Save logic needs to change slightly ---
        # Instead of iterating over available_templates, iterate over the dynamically generated fields.
        
        # Use a consistent way to determine the templates we are looking at.
        # We can use the template object we attached to the quantity field
        
        created_steps = []
        
        # Filter cleaned_data keys for quantity fields
        quantity_fields = sorted([k for k in self.cleaned_data if k.endswith('_quantity')])
        
        for quantity_field in quantity_fields:
            template = self.fields[quantity_field].template # Get the template instance we attached
            
            names_field = f'template_{template.id}_names'
            
            # The cleaned_data is now guaranteed to have these keys if the fields were valid
            quantity = self.cleaned_data.get(quantity_field)
            custom_names_text = self.cleaned_data.get(names_field, '').strip()
            
            # If the quantity is None or 0, skip
            if not quantity:
                continue
                
            # Rest of your existing logic for creating ProjectStep and ProjectTask instances:
            custom_names = [name.strip() for name in custom_names_text.split('\n') if name.strip()]
            
            for i in range(quantity):
                # Determine step title
                step_title = custom_names[i] if i < len(custom_names) else template.name
                
                # Determine step order
                current_max_order = ProjectStep.objects.filter(project=self.instance).aggregate(models.Max('order'))['order__max'] or 0
                step_order = current_max_order + 1 + len(created_steps)
                
                # Create the project step
                project_step = ProjectStep.objects.create(
                    project=self.instance,
                    step_template=template,
                    title=step_title,
                    icon=getattr(template, 'icon', ''), # Safely access icon if it exists
                    order=step_order
                )
                
                # Create tasks from template
                # Assuming 'tasks' is the related_name from StepTemplate to TaskTemplate
                task_templates = template.tasks.filter(is_active=True).order_by('order') 
                for j, task_template in enumerate(task_templates, start=1):
                    ProjectTask.objects.create(
                        project_step=project_step,
                        task_template=task_template,
                        title=task_template.title,
                        info_url=getattr(task_template, 'info_url', ''), # Safely access info_url
                        order=j
                    )
                
                created_steps.append(project_step)
        
        return self.instance


class QuickAddStepForm(forms.Form):
    """
    Quick form for adding a step via AJAX
    Used in the project setup page
    """
    
    step_template_id = forms.IntegerField(
        widget=forms.HiddenInput()
    )
    
    custom_title = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Custom name (optional)',
        }),
        label='Custom Name'
    )
    
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
    
    def clean_step_template_id(self):
        """Validate that the template exists and is active"""
        template_id = self.cleaned_data.get('step_template_id')
        
        try:
            template = StepTemplate.objects.get(id=template_id, is_active=True)
            self.template = template
            return template_id
        except StepTemplate.DoesNotExist:
            raise ValidationError('Invalid step template')
    
    def save(self):
        """Create the project step and associated tasks"""
        from .services import ProjectService
        
        custom_title = self.cleaned_data.get('custom_title')
        
        return ProjectService.add_step_to_project(
            project=self.instance,
            step_template=self.template,
            custom_title=custom_title
        )


class StepDuplicateForm(forms.Form):
    """
    Form for duplicating an existing step
    """
    
    step_id = forms.IntegerField(widget=forms.HiddenInput())
    
    custom_title = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-input',
            'placeholder': 'Name for duplicate (optional)',
        }),
        label='New Name'
    )
    
    def __init__(self, *args, **kwargs):
        self.instance = kwargs.pop('project', None)
        super().__init__(*args, **kwargs)
    
    def clean_step_id(self):
        """Validate step belongs to the project"""
        step_id = self.cleaned_data.get('step_id')
        
        try:
            step = ProjectStep.objects.get(id=step_id, project=self.instance)
            self.step = step
            return step_id
        except ProjectStep.DoesNotExist:
            raise ValidationError('Invalid step')
    
    def save(self):
        """Duplicate the step"""
        from .services import ProjectService
        
        custom_title = self.cleaned_data.get('custom_title')
        
        return ProjectService.duplicate_step(
            project_step=self.step,
            custom_title=custom_title
        )

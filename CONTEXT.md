# Project Documentation: Multi-Step Checklist Management System

## Project Overview

This project is a multi-step checklist management system designed to help users organize and execute complex workflows that consist of multiple sequential or parallel steps. Each step contains a list of tasks that need to be completed, with support for task status tracking (Done/N/A), comments, and reference documentation links.
Core Concept
Think of it as a recipe/procedure management system where:

A Project is like planning a dinner party
Steps are major phases (grocery shopping, cleaning, cooking, etc.)
Tasks are individual actions within each step
Steps can be instantiated multiple times (e.g., "Grocery Shopping - Day 1", "Grocery Shopping - Day 2")

## Key Features

✅ Predefined step templates with reusable task lists
✅ Multiple instances of steps per project
✅ Custom naming for step instances
✅ Task status tracking (Done, N/A, Pending)
✅ Comments on tasks (simple or YouTube-style discussion threads)
✅ Reference links for task documentation
✅ Visual progress tracking
✅ Color-coded step status (Not Started, In Progress, Completed)

## Objectives

### Primary Goals

Provide a template-based workflow system where admins can define reusable step and task templates
Allow users to create projects based on these templates with customization options
Enable flexible step instantiation - users can add 0 to N instances of each step type
Track execution progress with visual indicators and status management
Support collaborative features through comments and shared documentation

### Business Value

Standardize complex workflows across teams
Reduce errors by providing structured checklists
Track progress and completion metrics
Enable knowledge sharing through embedded documentation links
Support iterative processes (multiple instances of same step)

### Technical Goals

Build a maintainable, scalable Django application
Leverage Django Admin for template management
Create an intuitive, responsive UI for checklist execution
Implement efficient database queries for nested relationships
Support future enhancements (teams, notifications, reporting)

### User Story & Use Case

Primary Use Case: Dinner Party Planning
Scenario: Sarah is hosting a dinner party for 12 people and needs to organize all preparation tasks.

## Workflow:

1. Sarah creates a "Dinner Party" project

Selects from predefined step templates
Adds 2 instances of "Grocery Shopping" (Day 1 and Day 2)
Renames them: "Grocery Shopping - Fresh Items" and "Grocery Shopping - Dry Goods"
Adds single instances of: Clean House, Set Table, Prepare Appetizers, Cook Main Course, Bake Dessert, Final Touches

2. System automatically generates tasks

Each step instance gets populated with tasks from the template
"Grocery Shopping - Fresh Items" gets 7 tasks
"Bake Dessert" gets 10 tasks (cake recipe steps)
Total: ~50+ tasks across all steps

3. Sarah executes the checklist

Opens the checklist view with sidebar showing all steps
Steps are color-coded:

🔴 Red = Not Started (0% complete)

🟡 Yellow = In Progress (1-99% complete)

🟢 Green = Completed (100% complete)

Clicks on each step to view tasks
Marks tasks as Done or N/A
Adds comments like "Store was out of organic, bought regular"
Clicks info links for "How to frost a cake"

## Progress tracking

Sidebar shows "5 of 7 tasks" for each step
Progress bar shows overall completion
Step turns green when all tasks are Done or N/A

## Other Use Cases

- Software Deployment Checklist:

Steps: Pre-deployment checks, Database migration, Deploy staging, QA testing, Deploy production, Post-deployment verification
Multiple deployment instances for different environments

- Employee Onboarding:

Steps: HR paperwork, Equipment setup, Account creation, Training modules, Team introductions
Different task sets for different departments

- Home Renovation Project:

Steps: Planning & permits, Demolition, Electrical, Plumbing, Drywall, Painting, Flooring, Final inspection
Multiple rooms = multiple instances of each step

# Technical Stack

- Backend Framework: Django 5.0+
- Frontend: Django Templates Vanilla JavaScript + HTML5 + CSS3
- State Management:
  - Server-side: Django session
  - Client-side: localStorage for checklist state persistence
- Database: PostgreSQL (Production) / SQLite (Development)
- Deployment Stack: Docker

# Database Model

Entity Relationship Overview

```
StepTemplate (1) ─────< (N) TaskTemplate
      │
      │
      ↓ (template)
ProjectStep (1) ─────< (N) ProjectTask ─────< (N) TaskComment
      │                       │
      │                       │
Project (1) ─────< (N)        User (1)
      │
      │
    User (1)
```

# Table Definitions

**StepTemplate**
Master catalog of step types (managed by admins in Django Admin)

**TaskTemplate**
Master catalog of tasks for each step template

**Project**
Individual projects created by users

**ProjectStep**
Instances of steps within a project (0 to N instances per template)

**ProjectTask**
Individual task instances within project steps

**TaskComment**
Individual commments instances linked to a task (0 to N instances per task)

# App Responsibilities

`core/` - Shared Utilities
Purpose: Reusable components across all apps

`templates_management/` - Template Catalog
Purpose: Admin-managed library of reusable step and task templates

`projects/` - Project Management
Purpose: CRUD operations for projects and configuration

`checklists/` - Project Tasks
Purpose: CRUD operations for comments and more later

`accounts/` - User Management
Purpose: Override default User model and add custom permissions if needed

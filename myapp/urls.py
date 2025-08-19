from django.urls import path
import myapp.views as views

urlpatterns = [
    path('', views.get),
    path('getProjects', views.get_projects),
    path('getAllProjects', views.get_all_projects),
    path('getProjectDetails', views.get_project_details),
    path('getOwners', views.get_owners),
    path('getSummaryUsers', views.get_summary_users),
    path('getConversationUsers', views.get_conversation_users),
    path('getChecklistAssistantThreads', views.get_checklist_assistant_threads),
    path('getPinsUsers', views.get_pins_users),
]

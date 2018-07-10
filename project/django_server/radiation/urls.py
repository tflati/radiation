"""django_server URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url
from radiation import views

urlpatterns = [
    url(r'^clear_cache/', views.clear_cache),
    url(r'^get_projects/', views.get_projects),
    url(r"dataset_overview/", views.dataset_overview),
    url("^genes/([^/]*)/?(.*)", views.genes),
    url("^genes/", views.simple_genes),
    url(r"search_by_gene_symbol/", views.search_by_gene_symbol),
    url(r"see_gene_isoforms/", views.see_gene_isoforms),
    url("^transcripts/([^/]*)/?(.*)", views.transcripts),
    url(r"search_by_transcript_symbol/", views.search_by_transcript_symbol),
    url(r'^features/', views.features),
    url(r"search_by_feature/", views.search_by_feature),
    url(r"search_by_diff_fold_expr/", views.search_by_diff_fold_expr),
    url(r"search_by_condition/", views.search_by_condition),
    url(r"gene_plotter/", views.gene_plotter),
    url(r'^covariate_values/([^/]*)/?(.*)/', views.covariate_values),
    url(r'^covariates/([^/]*)/', views.covariates),
    url(r'^measures/', views.measures),
    url(r'^downloads/', views.downloads),
]

from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("categories/", views.ProductCategoryListView.as_view(), name="category_list"),
    path("categories/new/", views.ProductCategoryCreateView.as_view(), name="category_create"),
    path("categories/<int:pk>/edit/", views.ProductCategoryUpdateView.as_view(), name="category_update"),
    path("categories/<int:pk>/delete/", views.ProductCategoryDeleteView.as_view(), name="category_delete"),
    path("", views.ProductListView.as_view(), name="product_list"),
    path("new/", views.ProductCreateView.as_view(), name="product_create"),
    path("<int:pk>/", views.ProductDetailView.as_view(), name="product_detail"),
    path("<int:pk>/edit/", views.ProductUpdateView.as_view(), name="product_update"),
    path("<int:pk>/delete/", views.ProductDeleteView.as_view(), name="product_delete"),
    path("import/", views.ProductImportCsvView.as_view(), name="product_import"),
    path("export/", views.ProductExportCsvView.as_view(), name="product_export"),
]

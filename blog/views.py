from django.contrib.auth import get_user_model, login
from django.contrib.auth.mixins import (
    PermissionRequiredMixin, LoginRequiredMixin
)
from django.core.paginator import Paginator
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse_lazy, reverse
from django.views import generic

from blog.forms import CustomUserCreationForm, CommentaryForm, PostForm
from blog.models import Post, Commentary


class PostListView(generic.ListView):
    model = Post
    queryset = (
        Post.objects.select_related("owner").prefetch_related("commentary_set")
    )
    template_name = "blog/index.html"
    paginate_by = 5


class MyPostsListView(LoginRequiredMixin, generic.ListView):
    model = Post
    template_name = "blog/index.html"
    paginate_by = 5

    def get_queryset(self):
        return Post.objects.select_related(
            "owner"
        ).prefetch_related("commentary_set").filter(owner=self.request.user)


class PostDetailView(generic.DetailView):
    model = Post

    def get_queryset(self):
        return Post.objects.select_related(
            "owner"
        ).prefetch_related("commentary_set__user")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        post = self.get_object()
        comment_list = post.commentary_set.all()
        paginator = Paginator(comment_list, 3)
        page_number = self.request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        context["page_obj"] = page_obj
        context["paginator"] = paginator
        context["is_paginated"] = True
        context["form"] = CommentaryForm()
        return context


class CommentaryCreateView(generic.CreateView):
    form_class = CommentaryForm
    model = Commentary
    template_name = "blog/post_detail.html"

    def form_valid(self, form):
        form = self.form_class(self.request.POST)
        if form.is_valid():
            commentary = form.save(commit=False)
            commentary.user_id = self.request.user.id
            commentary.post_id = self.kwargs["pk"]
            commentary.save()

        return redirect("blog:post-detail", pk=self.kwargs["pk"])


class PostCreateView(LoginRequiredMixin, generic.CreateView):
    form_class = PostForm
    model = Post

    def form_valid(self, form):
        form = self.form_class(self.request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.owner_id = self.request.user.id
            post.save()

        return redirect("blog:index")


class PostUpdateView(PermissionRequiredMixin, generic.UpdateView):
    form_class = PostForm
    model = Post
    success_url = reverse_lazy("blog:index")

    def has_permission(self):
        post = self.get_object()
        return post.owner == self.request.user


class PostDeleteView(PermissionRequiredMixin, generic.DeleteView):
    model = Post
    success_url = reverse_lazy("blog:index")

    def has_permission(self):
        post = self.get_object()
        return post.owner == self.request.user


class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    model = get_user_model()
    template_name = "registration/sign_up.html"

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)

        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse("blog:index")


def about_view(request: HttpRequest):
    return render(request, "blog/about_template.html")

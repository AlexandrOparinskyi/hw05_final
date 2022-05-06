from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Comment, Follow, Group, Post, User


def paginate_queryset(request, post_list):
    post = Paginator(post_list, settings.POSTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = post.get_page(page_number)
    return page_obj


def index(request):
    post_list = Post.objects.select_related()
    return render(request, 'posts/index.html', {
        'page_obj': paginate_queryset(request, post_list)
    })


def group_list(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = group.posts.select_related('author')
    context = {
        'group': group,
        'page_obj': paginate_queryset(request, post_list),
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group')
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=get_object_or_404(User, username=username),
        )
    else:
        following = False
    context = {
        'page_obj': paginate_queryset(request, post_list),
        'author': author,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    comments = Comment.objects.filter(post=post_id)
    context = {
        'post': post,
        'form': form,
        'comments': comments,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=post.author.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if not request.user == post.author:
        return redirect('posts:post_detail', post_id=post.pk)
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        post.save()
        return redirect('posts:post_detail', post_id=post.pk)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    page_obj = (
        Post.objects.select_related()
        .filter(author__following__user=request.user)
    )
    context = {
        'page_obj': paginate_queryset(request, page_obj)
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    Follow.objects.create(
        user=request.user,
        author=get_object_or_404(User, username=username),
    )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    if (Follow.objects.filter(
        user=request.user,
        author=get_object_or_404(User, username=username),
    ).exists()):
        Follow.objects.filter(
            user=request.user,
            author=get_object_or_404(User, username=username),
        ).delete()
    return redirect('posts:profile', username=username)

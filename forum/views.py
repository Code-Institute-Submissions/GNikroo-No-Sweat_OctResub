'''Views for No Sweat fitforum'''
from django.shortcuts import render, get_object_or_404, reverse
from django.contrib import messages
from django.views import generic, View
from django.http import HttpResponseRedirect
from django.db.models import Q
from django.utils.text import slugify
from .models import Post, Comment
from .forms import CommentForm, PostForm, UpdateForm, UpdateCommentForm


class Search(View):
    """Creates a list of search results."""
    def get(self, request):
        """
        Retrieves query via user input and
        checks against title, content, and label.
        Returns a list of matching posts at
        six per page.
        """
        query = request.GET.get('query', '')

        if query:
            posts = Post.objects.all().filter(Q(title__icontains=query) | Q(content__icontains=query) | Q(label__icontains=query))  # noqa
        else:
            posts = []

        return render(
            request,
            "index.html",
            {
                "query": query,
                "posts": posts,
                "searched": True,
            },
        )


class PostList(generic.ListView):
    '''A list of six of the most recent posts per page.'''
    model = Post
    queryset = Post.objects.all().order_by('-created_on')
    template_name = "index.html"
    paginate_by = 6


class UserPostList(View):
    '''
    The authenticated user's profile.
    Six of the most recent posts per page.
    '''
    def get(self, request):
        '''
        Displays all posts wherein the user's
        id matches the post's author.
        '''
        queryset = Post.objects.all()

        if queryset:
            posts = Post.objects.filter(author=request.user.id).order_by('-created_on')  # noqa

        else:
            posts = []

        return render(
            request,
            "user_profile.html",
            {
                "queryset": queryset,
                "posts": posts,
            }
        )


class TagSearch(View):
    def get(self, request):
        '''
        Retrieves a queryset via a form
        generated by the existance of a label.
        Returns a list of matching posts at
        six per page.
        '''
        queryset = request.GET.get('queryset', '')
        posts = Post.objects.filter(label__icontains=queryset)

        return render(
            request,
            "tag_search.html",
            {
                "queryset": queryset,
                "posts": posts,
                "tag_request": True,
            },
        )


class AddPost(View):
    '''
    Displays and submits the form to add an original post.
    '''
    def get(self, request, *args, **kwargs):
        '''Displays the add post form.'''
        post_form = PostForm()
        return render(
            request,
            'add_post.html',
            {
                'post_form': post_form,
            },
        )

    def post(self, request, *args, **kwargs):
        '''
        Submits the post details to the database
        and informs the user of whether or
        not the submission was successful.
        Redirects the user to their profile.
        '''
        post_form = PostForm(request.POST, request.FILES)
        if post_form.is_valid():
            post_form.instance.author = request.user
            post = post_form.save(commit=False)
            post.slug = slugify(post.title)
            post_form.post = post
            post_form.save()
            messages.success(request, "Your post has been added!")
        else:
            post_form = PostForm()
            messages.error(request, 'Invalid form submission.')

        return HttpResponseRedirect('/user_profile')


class UpdatePost(View):
    '''Displays and submits the form to update a post.'''
    def get(self, request, *args, **kwargs):
        '''
        Retrieves the specified post's slug in
        order to verify which post is being
        updated. Displays the form to update
        which is prepopulated with the post's
        details.
        '''
        slug = kwargs.get('slug')
        post_to_update = Post.objects.get(slug=slug)
        update_form = UpdateForm(initial={
            'title': post_to_update.title,
            'featured_image': post_to_update.featured_image,
            'content': post_to_update.content,
        })

        return render(
            request,
            'update_post.html',
            {
                'update_form': update_form,
            },
        )

    def post(self, request, *args, **kwargs):
        '''
        Verifies that the updated post details
        belong to the correct post. Authenticates
        the user based on whether they are the
        original author. Informs the user of
        whether or not the submission was successful.
        Redirects to user profile.
        '''
        slug = kwargs.get('slug')
        post_object = Post.objects.get(slug=slug)
        update_form = UpdateForm(request.POST, request.FILES, instance=post_object)  # noqa
        if update_form.is_valid():
            update_form.instance.author = request.user
            post = update_form.save(commit=False)
            post.slug = slugify(post.title)
            update_form.post = post
            update_form.save()
            messages.success(request, "Your post has been updated!")
        else:
            update_form = UpdateForm()
            messages.error(request, 'Invalid form submission.')

        return HttpResponseRedirect('/user_profile')


class DeletePost(View):
    '''Displays and submits the form to delete a post.'''
    def get(self, request, *args, **kwargs):
        '''
        Renders the delete post page which verifies
        the user intends to delete a post forever.
        '''
        return render(
            request,
            'delete_post.html',
        )

    def post(self, request, *args, **kwargs):
        '''
        Verifies that the deleted post details
        belong to the correct post. Informs the user
        if the submission was successful.
        Redirects to user profile.
        '''
        slug = kwargs.get('slug')
        post_to_delete = Post.objects.get(slug=slug)
        post_to_delete.delete()
        messages.success(request, 'Your post has been deleted.')
        return HttpResponseRedirect('/user_profile')


class UpdateComment(View):
    '''Displays and submits the form to update a comment.'''
    def get(self, request, **kwargs):
        '''
        Retrieves the specified post's primary key
        in order to verify which comment is being
        updated. Displays the form to update
        which is prepopulated with the comment's
        details.
        '''
        comment_id = kwargs.get('pk')
        comment_obj = Comment.objects.get(pk=comment_id)
        update_comment_form = UpdateCommentForm(initial={
            'body': comment_obj.body,
        })

        return render(
            request,
            'update_comment.html',
            {
                'update_comment_form': update_comment_form,
            },
        )

    def post(self, request, **kwargs):
        '''
        Verifies that the updated comment correlates
        to the correct post and the comment primary
        key. Authenticates the user based on whether
        they are the original owner of the comment.
        Informs the user of whether or not the
        submission was successful. Redirects to user
        profile.
        '''
        slug = kwargs.get('slug')
        comment_id = kwargs.get('pk')
        comment_obj = Comment.objects.get(pk=comment_id)
        update_comment_form = UpdateCommentForm(request.POST, instance=comment_obj)  # noqa
        if update_comment_form.is_valid():
            if comment_obj.name == request.user.username:
                update_comment_form.instance.owner = request.user
                comment_obj = update_comment_form.save(commit=False)
                update_comment_form.comment = comment_obj
                update_comment_form.save()
                messages.success(request, "Your comment has been updated!")
        else:
            update_comment_form = UpdateCommentForm()
            messages.error(request, 'Invalid form submission.')

        return HttpResponseRedirect(f"/{slug}")


class DeleteComment(View):
    '''Displays and submits the form to delete a comment.'''
    def get(self, request, *args, **kwargs):
        '''
        Renders the delete comment page which verifies
        the user intends to delete a comment forever.
        '''
        return render(
            request,
            'delete_comment.html',
        )

    def post(self, request, *args, **kwargs):
        '''
        Verifies that the deleted comment correlates
        to the correct post and the comment primary
        key. Informs the user if the submission was
        successful. Redirects to the post the
        deleted comment was attached to.
        '''
        slug = kwargs.get('slug')
        comment_id = kwargs.get('pk')
        comment_to_delete = Comment.objects.get(pk=comment_id)
        comment_to_delete.delete()
        messages.success(request, 'Your comment has been deleted.')
        return HttpResponseRedirect(f'/{slug}')


class PostDetail(View):
    '''Displays the post details'''
    def get(self, request, slug, *args, **kwargs):
        '''
        Retrieves post based on it's slug. Displays
        comments, comment count, and like count. Allows
        user to like or unlike.
        '''
        queryset = Post.objects.all()
        post = get_object_or_404(queryset, slug=slug)
        comments = post.comments.order_by('created_on')
        liked = False
        if post.likes.filter(id=self.request.user.id).exists():
            liked = True
        return render(
            request,
            "post_detail.html",
            {
                "post": post,
                "comments": comments,
                "liked": liked,
                "comment_form": CommentForm(),
            },
        )

    def post(self, request, slug, *args, **kwargs):
        '''
        Renders and submits comment form. Creates
        a name instance based on the user's username.
        Informs the user whether or not the submission
        was successful. Returns user to the post the
        new comment is attached to.
        '''
        queryset = Post.objects.all()
        post = get_object_or_404(queryset, slug=slug)
        comments = post.comments.order_by('created_on')
        liked = False
        if post.likes.filter(id=self.request.user.id).exists():
            liked = True

        comment_form = CommentForm(data=request.POST)

        if comment_form.is_valid():
            comment_form.instance.name = request.user.username
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.save()
            messages.success(request, "Your comment has been added!")
        else:
            comment_form = CommentForm()

        return render(
            request,
            "post_detail.html",
            {
                "post": post,
                "comments": comments,
                "commented": True,
                "comment_form": comment_form,
                "liked": liked,
            },
        )


class PostLike(View):
    '''
    Allows authenticated users to like and unlike posts.
    '''
    def post(self, request, slug):
        '''
        Retrieves a post based on it's slug. Verifies
        if a user has previously liked the post to
        determine whether or not the post has been liked
        or unliked when the button is interacted with.
        '''
        post = get_object_or_404(Post, slug=slug)
        if post.likes.filter(id=request.user.id).exists():
            post.likes.remove(request.user)
        else:
            post.likes.add(request.user)

        return HttpResponseRedirect(reverse('post_detail', args=[slug]))

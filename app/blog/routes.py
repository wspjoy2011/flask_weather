import os
from time import time

from flask_paginate import get_page_parameter, Pagination
from werkzeug.utils import secure_filename
from flask_login import login_required, current_user
from flask import render_template, flash, redirect, url_for, request, current_app, abort, make_response

from app.blog import blog
from app.blog.models import Post
from app.blog.forms import PostForm
from app.auth.models import User
from app.main.utils import parse_range_from_paginator
from app.auth.utils import check_permissions
from app.blog.services import get_followers, get_followed, get_followers_count, get_followed_count


@blog.route('/', methods=['GET', 'POST'])
@login_required
def index():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(
            body=form.body.data,
            author=current_user)

        if form.image.data:
            image_data = request.files[form.image.name].read()
            image_name = f'{round(time())}_{secure_filename(request.files[form.image.name].filename.strip())}'
            url_to_image = current_app.config['UPLOAD_URL_BLOG'] + image_name
            path_to_file = os.path.join(current_app.config['UPLOAD_FOLDER_BLOG'], image_name)
            open(path_to_file, 'wb').write(image_data)
            post.image = url_to_image

        post.save()
        flash('Post added')
        return redirect(url_for('blog.index'))

    show_followed = bool(request.cookies.get('show_followed', ''))

    if show_followed:
        posts = current_user.followed_posts
    else:
        posts = Post.select().order_by(Post.timestamp.desc())

    page = request.args.get(get_page_parameter(), type=int, default=1)
    pagination = Pagination(page=page, total=len(posts), record_name='posts')
    start, stop = parse_range_from_paginator(pagination.info)

    return render_template(
        'blog/show_blogs.html',
        title='Blogs',
        posts=posts[start:stop],
        pagination=pagination,
        show_followed=show_followed,
        form=form)


@blog.route('/show/all')
@login_required
def show_all():
    response = make_response(redirect(url_for('.index')))
    response.set_cookie('show_followed', '', max_age=30 * 24 * 60 * 60)  # 30 days
    return response


@blog.route('/show/followed')
@login_required
def show_followed():
    response = make_response(redirect(url_for('.index')))
    response.set_cookie('show_followed', '1', max_age=30 * 24 * 60 * 60)  # 30 days
    return response


@blog.route('/user/<username>')
def user_blog(username):
    user = User.select().where(User.name == username.lower()).first()
    if not user:
        abort(404)

    page = request.args.get(get_page_parameter(), type=int, default=1)

    posts = Post.select().where(Post.author == user).order_by(Post.timestamp.desc())

    pagination = Pagination(page=page, total=posts.count(), record_name='posts')
    start, stop = parse_range_from_paginator(pagination.info)

    followers_count = get_followers_count(user)
    followed_count = get_followed_count(user)
    return render_template(
        'blog/user_blog.html',
        user=user,
        title=f'Blog by {user.name}',
        posts=posts[start:stop],
        followers_count=followers_count,
        followed_count=followed_count,
        pagination=pagination)


@blog.route('/post/<int:post_id>')
def post(post_id):
    post = Post.select().where(Post.id == post_id).first()
    if not post:
        abort(404)
    return render_template(
        'blog/post.html',
        title=f'Post by {post.author.name}',
        author=post.author.name,
        posts=[post])


@blog.route('/post/edit/<int:post_id>', methods=['GET', 'POST'])
@login_required
def edit(post_id):
    post = Post.select().where(Post.id == post_id).first()
    if not post:
        abort(404)

    if current_user.id != post.author.id or \
            not check_permissions(current_user.id):
        abort(403)

    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        post.save()
        flash('The post has been updated.')
        return redirect(url_for('blog.post', post_id=post.id))

    form.body.data = post.body
    return render_template(
        'blog/edit_post.html',
        title=f'Edit post {post.id}',
        post=post,
        form=form)


@blog.route('/follow/<username>')
@login_required
def follow(username: str):
    username = username.lower()
    user = User.select().where(User.name == username).first()

    if user is None:
        flash(f'Invalid user {username}')
        return redirect(url_for('blog.index'))

    if current_user.is_following(user):
        flash(f'You are already following user {username}')
        return redirect(url_for('blog.user_blog', username=username))

    current_user.follow(user)
    flash(f'You are now following user {username}')
    return redirect(url_for('blog.user_blog', username=username))


@blog.route('/unfollow/<username>')
@login_required
def unfollow(username: str):
    username = username.lower()
    user = User.select().where(User.name == username).first()
    if user is None:
        flash(f'Invalid user {username}')
        return redirect(url_for('blog.index'))

    if not current_user.is_following(user):
        flash(f'You are not following user {username}')
        return redirect(url_for('blog.user_blog', username=username))

    current_user.unfollow(user)
    flash(f'You are not following {username} anymore.')
    return redirect(url_for('blog.user_blog', username=username))


@blog.route('/followers/<username>')
@login_required
def followers(username: str):
    username = username.lower()
    user = User.select().where(User.name == username).first()

    if user is None:
        flash(f'Invalid user {username}')
        return redirect(url_for('blog.index'))

    page = request.args.get(get_page_parameter(), type=int, default=1)
    follows = get_followers(user)

    pagination = Pagination(page=page, total=len(follows), record_name='follows')
    start, stop = parse_range_from_paginator(pagination.info)
    return render_template(
        'blog/followers.html',
        title=f'Followers by {username}',
        follows=follows[start:stop],
        pagination=pagination
    )


@blog.route('/followed/<username>')
@login_required
def followed(username: str):
    username = username.lower()
    user = User.select().where(User.name == username).first()

    if user is None:
        flash(f'Invalid user {username}')
        return redirect(url_for('blog.index'))

    page = request.args.get(get_page_parameter(), type=int, default=1)
    follows = get_followed(user)

    pagination = Pagination(page=page, total=len(follows), record_name='follows')
    start, stop = parse_range_from_paginator(pagination.info)
    return render_template(
        'blog/followers.html',
        title=f'Followed by {username}',
        follows=follows[start:stop],
        pagination=pagination
    )

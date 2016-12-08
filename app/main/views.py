#!/usr/bin/python
# -*- coding: utf-8 -*-

from datetime import datetime
from flask import  render_template, session, url_for, redirect, flash, abort, request, make_response
from flask_login import login_required, current_user, current_app
from . import main
from forms import NameForm, EditProfileForm, EditProfileAdminForm, PostForm, CommentForm, UploadForm
from .. import db
from ..models import User, Role, Permission, Post
from ..email import send_emial
from ..decorators import admin_required, permission_required
from werkzeug import security
import os
import uuid
from PIL import Image

#*********************
ALLOWED_EXTENSIONS = set(['png','jpg', 'jpeg'])
UPLOAD_FOLDER = 'C:/Users/jd/PycharmProjects/flask_web/uplodes'
HEAD_IMG_ADDRESS = 'C:/Users/jd/PycharmProjects/flask_web/app/static'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

@main.route('/', methods=['GET', 'POST'])
def index():
    form = PostForm()
    show_followed = False
    print current_user
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        post = Post(body=form.body.data,
                    author=current_user._get_current_object())
        db.session.add(post)
        return redirect(url_for('.index'))
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query
    page = request.args.get('page', 1, type=int)
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'])
    posts = pagination.items
    return render_template('index.html', form=form, posts=posts, pagination=pagination)

@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp

@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp

@main.route('/user/<username>')
def user(username):
    '''用户资料'''
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)

@main.route('/edit-profile/', methods=['GET', 'POST'])
@login_required
def edit_profile():
    '''更改个人资料的页面'''
    form = EditProfileForm()
    form_head = UploadForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash(u"你的个人资料已经更新")
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form, form_head=form_head)

def hash_filename(filename):
    '''
    为防止图片名称重复，根据上传图片名称，生成唯一哈希图片名称
    如
    In    xianth.jpg
    Out    22a4f83beda449c497b5d784aefbf916.jpg

    In    C:/Users/jd/PycharmProjects/web/templates/xianth.jpg
    Out    17ba8a98b22d4ff6bd26168278f8f862.jpg
    :param filename:
    :return:
    '''
    _, _, suffix = filename.rpartition('.')
    return '{}.{}'.format(uuid.uuid4().hex, suffix)

def creat_head_img(upload_img, head_img_address):
    '''
    根据已上传图片，生成不同大小的头像与头像略缩图，并保存在数据库中
    :param upload_img: 已上传图片地址
    :param head_img_address: 略缩图与头像保存目录
    :return: 一个元组，两个元素分别是头像保存地址与略缩图保存地址  （头像地址， 略缩图地址）
    '''
    load_img_name = hash_filename(upload_img)
    name, _, suffix = load_img_name.rpartition('.')
    load_img_yuesuo_name = name + 'YUESUO.' + suffix
    #给头像和略缩图命名
    size = (256, 256)       #头像尺寸
    size_yuesuo = (40, 40)          #略缩图尺寸
    img = Image.open(upload_img, 'r')

    new_img = img.resize(size)
    new_img.save(os.path.join(head_img_address, load_img_name))
    new_img_yuesuo = img.resize(size_yuesuo)
    new_img_yuesuo.save(os.path.join(head_img_address, load_img_yuesuo_name))
    return load_img_name, load_img_yuesuo_name

@main.route('/upload-head/', methods=['GET', 'POST'])
@login_required
def upload_head():
    '''
    专门处理图片上传
    :return: 返回到修改资料页面
    '''
    if request.method == 'POST':
        file = request.files['file']
        print file.filename
        if not file or file.filename.rsplit('.', 1)[1] not in ALLOWED_EXTENSIONS:
            flash(u'图片格式错误！')
            return redirect(url_for('.edit_profile'))
        file.filename = file.filename
        upload_img = os.path.join(UPLOAD_FOLDER, file.filename)
        file.save(upload_img)
        current_user.head, current_user.head_yuesuo = creat_head_img(upload_img, HEAD_IMG_ADDRESS)
        db.session.add(current_user)
        flash(u'你已经上传图片')
    return redirect(url_for('.edit_profile'))



#管理员更改资料的页面
@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.ADMINISTER)
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    if user is None:
        print"++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++"
        abort(404)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash(u'资料已经更改完毕！')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit_profile.html', form=form, user=user)

#单独文章的URL路由
@main.route('/post/<int:id>')
def post(id):
    post = Post.query.get_or_404(id)
    # form = CommentForm
    # if form.validate_on_submit():
    #     comment = CommentForm(body=form.body.data,
    #                           post=post,
    #                           author=current_user._get_current_object())
    #     db.session.add(comment)
    #     flash(u'你已经发表了评论！')
    #     return redirect(url_for('.post', id=post.id, page=-1))
    # page = request.args.get('page', 1, type=int)
    # if page == -1:
    #     page = (post.comments.count()-1)/current_app.config['FLASK_POSTS_PER_PAGE'] + 1
    # pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
    #     page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'], error_out=False)
    # comments = pagination.items
    return render_template('post.html', posts=[post])

@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    post = Post.query.get_or_404(id)
    if current_user != post.author and \
            not current_user.can(Permission.ADMINISTER):
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))
    form.body.data = post.body
    return render_template('edit_post.html', form=form)

#实现关注功能的路由
@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(u'检索不到该用户！')
        return redirect(url_for('.index'))
    if current_user.is_following(user):
        flash(u'你已经关注了该用户！')
        return redirect(url_for('.user', username=username))
    current_user.follow(user)
    flash(u'你已经关注了XXX ')
    return redirect(url_for('.user', username=username))

#实现取消关注功能
@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(u'检索不到该用户！')
        return redirect(url_for('.index'))
    if not current_user.is_following(user):
        flash(u'你并没有关注该用户！')
        return redirect(url_for('.user', username=username))
    current_user.unfollow(user)
    flash(u'你已经取消了对该用户的的关注 ')
    return redirect(url_for('.user', username=username))

@main.route('/followers/<username>')
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(u'该用户不存在！')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'], error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('followers.html', user=user, title="Followers of", endpoint='.followers',
                           pagination=pagination, follows=follows)


@main.route('/followed_by/<username>')
def followed_by(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(u'该用户不存在！')
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'], error_out=False)
    followed = [{'user': item.followed, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('followers.html', user=user, title="Followed by", endpoint='.followed_by',
                           pagination=pagination, follows=followed)













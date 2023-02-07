from flask import render_template, redirect, url_for, flash, request, current_app
from datetime import datetime
from flask_paginate import Pagination, get_page_parameter
from flask_login import login_required, current_user

from app.main import main
from app.main.forms import NameForm, GenerateDataForm
from app.auth.models import User, Role
from app.main.utils import parse_range_from_paginator
from app.auth.utils import check_permissions
from generate_data.db.create_test_database import create_db, USERS, PROFILES, ROLES
from weather.fill_country_db import main as fill_country_db, FILENAME as COUNTRY_JSON_FILE


@main.route('/', methods=['POST', 'GET'])
def index():
    """Home page"""
    form = GenerateDataForm()

    if form.validate_on_submit():
        db = current_app.config['db']
        create_db(db, USERS, PROFILES, ROLES, delete=True)
        fill_country_db(COUNTRY_JSON_FILE, db)
        flash('Database filled with test data')

    return render_template(
        'index.html',
        title='Home page',
        current_time=datetime.utcnow(),
        form=form
    )


@main.route('/email/show')
def show_emails():
    """Show user information"""
    page = request.args.get(get_page_parameter(), type=int, default=1)

    users = User.select()
    pagination = Pagination(page=page, total=users.count(), record_name='users')
    start, stop = parse_range_from_paginator(pagination.info)
    return render_template(
        'main/show_emails.html',
        title='Show users',
        users=users[start:stop],
        pagination=pagination,
    )


@main.route('/email/edit/<int:user_id>')
@login_required
def edit_email(user_id):
    """Edit user"""
    if not check_permissions(current_user):
        flash('You don\'t have access to edit this item.', 'error')
        return redirect(url_for('main.index'))

    user = User.select().where(User.id == user_id).first()
    if not user:
        flash(f'User with id: {user_id} not found.')
        return redirect(url_for('main.index'))

    form = NameForm()
    form.id.label.text = ''
    form.id.data = user.id
    form.name.data = user.name
    form.email.data = user.email
    form.role.choices = [(role.id, role.name) for role in Role.select()]
    form.role.choices = [(role_id, role_name) for role_id, role_name in form.role.choices
                         if role_id != user.role.id]
    form.role.choices.insert(0, (user.role.id, user.role.name))
    return render_template(
        'main/edit_email.html',
        title=f'Edit user {user.name}',
        form=form
    )


@main.route('/email/update', methods=['POST'])
@login_required
def update_email():
    """Update user from form"""
    form = NameForm()
    form.role.choices = [(role.id, role.name) for role in Role.select()]
    if form.validate_on_submit():
        user_id = form.id.data
        user_name = form.name.data
        user_email = form.email.data
        user_role_id = form.role.data

        role = Role.select().where(Role.id == user_role_id).first()
        user = User.select().where(User.id == user_id).first()

        user.name = user_name
        user.email = user_email
        user.role = role

        try:
            user.save()
            flash(f'{user_name} updated')
        except Exception:
            flash('Email already added into database')
    else:
        flash(form.errors)
    return redirect(url_for('main.index'))


@main.route('/email/delete', methods=['POST'])
@login_required
def delete_emails():
    """Delete selected users"""
    if request.method == 'POST':
        if not check_permissions(current_user):
            flash('You don\'t have access to delete this users.', 'error')
            return redirect(url_for('main.index'))

        message = 'Deleted: '
        selectors = list(map(int, request.form.getlist('selectors')))

        if not selectors:
            flash('Nothing to delete')
            return redirect(url_for('main.show_emails'))

        for selector in selectors:
            user = User.get(User.id == selector)
            message += f'{user.email} '
            user.delete_instance()

        flash(message)
        return redirect(url_for('main.show_emails'))

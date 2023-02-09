from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, FileField
from wtforms.validators import DataRequired
from flask_pagedown.fields import PageDownField


class PostForm(FlaskForm):
    image = FileField('Image', render_kw={'class': 'form-control'})
    body = PageDownField(
        "What's on your mind?",
        validators=[DataRequired()],
        render_kw={'rows': '8'}
    )
    submit = SubmitField(
        'Add',
        render_kw={'id': 'addImage'}
    )


class CommentForm(FlaskForm):
    body = PageDownField(
        'Comment',
        validators=[DataRequired()],
        render_kw={'rows': '3'}
    )
    submit = SubmitField('Add comment')

from flask import render_template, request, jsonify


def internal_server_error(error):
    """Internal server error handler"""
    if request.path.startswith('/api_blog/'):
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template(
        'error.html',
        title='Error 500',
        error=error
    ), 500


def page_not_found(error):
    """Page not found error handler"""
    if request.path.startswith('/api_blog/'):
        response = jsonify({'error': 'not found'})
        response.status_code = 404
        return response
    return render_template(
        'error.html',
        title='Error 404',
        error=error
    ), 404


def forbidden(error):
    """Forbidden resource error handler"""
    if request.path.startswith('/api_blog/'):
        response = jsonify({'error': 'forbidden'})
        response.status_code = 403
        return response
    return render_template(
        'error.html',
        title='Error 403',
        error=error
    ), 403


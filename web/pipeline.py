from social_core.exceptions import AuthAlreadyAssociated

def prevent_double_associating(backend, uid, is_new: bool, new_association: bool, user=None, social=None, *args, **kwargs):
    ''' Disallow creating a new social association for an existing user '''

    if new_association and not is_new:
        raise AuthAlreadyAssociated(backend, 'This user is already associated with an external account.')

    return {'social': social,
        'user': user,
        'is_new': is_new,
        'new_association': new_association}

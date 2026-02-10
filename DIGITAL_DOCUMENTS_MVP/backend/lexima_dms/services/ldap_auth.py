"""LDAP/AD DS authentication."""

from __future__ import annotations

from lexima_dms.app_core.config import get_settings


def authenticate_ldap(username: str, password: str) -> bool:
    """
    Authenticate user against LDAP/AD DS.
    Returns True if credentials are valid.
    """
    settings = get_settings()
    if not settings.ldap_enabled or not settings.ldap_url:
        return False

    try:
        import ldap3
    except ImportError:
        return False

    server = ldap3.Server(settings.ldap_url)
    search_filter = settings.ldap_user_search_filter.format(username=ldap3.utils.conv.escape_filter_chars(username))

    if settings.ldap_bind_dn and settings.ldap_bind_password:
        # Bind with service account, search for user, then verify with user password
        conn = ldap3.Connection(
            server,
            user=settings.ldap_bind_dn,
            password=settings.ldap_bind_password,
            auto_bind=True,
        )
        conn.search(
            search_base=settings.ldap_base_dn,
            search_filter=search_filter,
            search_scope=ldap3.SUBTREE,
            attributes=["distinguishedName"],
        )
        if not conn.entries:
            conn.unbind()
            return False
        user_dn = str(conn.entries[0].distinguishedName)
        conn.unbind()

        # Verify password by binding as user
        user_conn = ldap3.Connection(server, user=user_dn, password=password, auto_bind=True)
        user_conn.unbind()
        return True
    else:
        # Direct bind: use ldap_user_dn_template (e.g. "{username}@corp.local")
        if settings.ldap_user_dn_template:
            user_dn = settings.ldap_user_dn_template.format(username=username)
            try:
                conn = ldap3.Connection(
                    server,
                    user=user_dn,
                    password=password,
                    auto_bind=True,
                )
                conn.unbind()
                return True
            except Exception:
                pass
        return False

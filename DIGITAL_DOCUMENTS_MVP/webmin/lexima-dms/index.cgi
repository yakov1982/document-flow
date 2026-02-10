#!/usr/bin/perl
#
# Webmin module for DIGITAL DOCUMENTS MVP configuration
# Install: cp -r lexima-dms /usr/share/webmin/
#

use strict;
use warnings;
no warnings 'redefine';

use WebminCore;
init_config();

# Resolve env file path
sub get_env_path {
    my $bp = $config{'backend_path'};
    $bp = $in{'backend_path'} if $ENV{'REQUEST_METHOD'} eq 'POST' && $in{'backend_path'};
    return undef unless $bp && -d $bp;
    return "$bp/.env";
}

# Read current .env
sub read_env {
    my $env_file = get_env_path();
    my %vars;
    return %vars unless $env_file && -r $env_file;
    open my $fh, '<', $env_file or return %vars;
    while (<$fh>) {
        chomp;
        next if /^\s*#/ || /^\s*$/;
        if (/^([A-Za-z0-9_]+)=(.*)$/) {
            my ($k, $v) = ($1, $2);
            $v =~ s/^"(.*)"$/$1/;
            $v =~ s/^'(.*)'$/$1/;
            $vars{$k} = $v;
        }
    }
    close $fh;
    return %vars;
}

# Write .env
sub write_env {
    my %vars = @_;
    my $env_file = get_env_path();
    return 0 unless $env_file;

    my $bak = "$env_file.bak." . time();
    if (-f $env_file) {
        rename($env_file, $bak) or return 0;
    } else {
        my $dir = $config{'backend_path'};
        $dir = $in{'backend_path'} if $ENV{'REQUEST_METHOD'} eq 'POST' && $in{'backend_path'};
        return 0 unless $dir && -d $dir;
    }

    open my $fh, '>', $env_file or return 0;
    print $fh "# DIGITAL DOCUMENTS MVP - edited via Webmin\n";
    print $fh "#\n";
    print $fh "# JWT\n";
    for my $k (qw(LEXIMA_DMS_DATA_DIR LEXIMA_DMS_JWT_SECRET LEXIMA_DMS_JWT_ALG LEXIMA_DMS_JWT_EXPIRES_MINUTES)) {
        my $v = $vars{$k} || '';
        $v = "\"$v\"" if $v =~ /\s/;
        print $fh "$k=$v\n";
    }
    print $fh "#\n# LDAP/AD DS\n";
    for my $k (qw(LEXIMA_DMS_LDAP_ENABLED LEXIMA_DMS_LDAP_URL LEXIMA_DMS_LDAP_BASE_DN
        LEXIMA_DMS_LDAP_BIND_DN LEXIMA_DMS_LDAP_BIND_PASSWORD
        LEXIMA_DMS_LDAP_USER_SEARCH_FILTER LEXIMA_DMS_LDAP_USER_DN_TEMPLATE LEXIMA_DMS_LDAP_DEFAULT_ROLE)) {
        my $v = $vars{$k} || '';
        $v = "\"$v\"" if $v =~ /\s/;
        print $fh "$k=$v\n";
    }
    close $fh;
    return 1;
}

# Save module config (backend_path)
sub save_module_config {
    my $bp = shift;
    my $cf = $config_directory . "/config";
    $cf = "/etc/webmin/lexima-dms/config" unless $config_directory;
    open my $fh, '>', $cf or return 0;
    print $fh "backend_path=$bp\n" if $bp;
    close $fh;
    return 1;
}

my @config_keys = (
    qw(LEXIMA_DMS_DATA_DIR LEXIMA_DMS_JWT_SECRET LEXIMA_DMS_JWT_ALG LEXIMA_DMS_JWT_EXPIRES_MINUTES
       LEXIMA_DMS_LDAP_URL LEXIMA_DMS_LDAP_BASE_DN LEXIMA_DMS_LDAP_BIND_DN LEXIMA_DMS_LDAP_BIND_PASSWORD
       LEXIMA_DMS_LDAP_USER_SEARCH_FILTER LEXIMA_DMS_LDAP_USER_DN_TEMPLATE LEXIMA_DMS_LDAP_DEFAULT_ROLE)
);

if ($ENV{'REQUEST_METHOD'} eq 'POST' && $in{'save'}) {
    my $bp = $in{'backend_path'};
    $config{'backend_path'} = $bp if $bp;
    save_module_config($bp) if $bp;

    my %vars = read_env();
    for my $k (@config_keys) {
        $vars{$k} = $in{$k} if defined $in{$k};
    }
    $vars{'LEXIMA_DMS_LDAP_ENABLED'} = $in{'LEXIMA_DMS_LDAP_ENABLED'} ? 'true' : 'false';

    if (get_env_path() && write_env(%vars)) {
        redirect($ENV{'SCRIPT_NAME'} . '?saved=1');
    } else {
        print header();
        print $text{'lexima_dms_error'}, ": ", "Cannot write .env. Check backend path.";
        exit;
    }
}

my %vars = read_env();
$vars{'LEXIMA_DMS_DATA_DIR'} ||= './data';
$vars{'LEXIMA_DMS_JWT_SECRET'} ||= 'change-me';
$vars{'LEXIMA_DMS_JWT_ALG'} ||= 'HS256';
$vars{'LEXIMA_DMS_JWT_EXPIRES_MINUTES'} ||= '720';
$vars{'LEXIMA_DMS_LDAP_USER_SEARCH_FILTER'} ||= '(sAMAccountName={username})';

print header();
print '<form method="post" class="form">';
print '<input type="hidden" name="save" value="1">';

print '<h2>', $text{'lexima_dms_backend_path'}, '</h2>';
print '<table>';
print '<tr><td>', $text{'lexima_dms_backend_path_desc'}, '</td><td>';
print '<input type="text" name="backend_path" value="', quote_escape($config{'backend_path'}), '" size="60">';
print '</td></tr>';
print '</table>';

print '<h2>', $text{'lexima_dms_jwt'}, '</h2>';
print '<table>';
print '<tr><td>', $text{'lexima_dms_data_dir'}, '</td><td>';
print '<input type="text" name="LEXIMA_DMS_DATA_DIR" value="', quote_escape($vars{'LEXIMA_DMS_DATA_DIR'}), '" size="40">';
print '</td></tr>';
print '<tr><td>', $text{'lexima_dms_jwt_secret'}, '</td><td>';
print '<input type="password" name="LEXIMA_DMS_JWT_SECRET" value="', quote_escape($vars{'LEXIMA_DMS_JWT_SECRET'}), '" size="40" autocomplete="off">';
print '</td></tr>';
print '<tr><td>', $text{'lexima_dms_jwt_expires'}, '</td><td>';
print '<input type="text" name="LEXIMA_DMS_JWT_EXPIRES_MINUTES" value="', quote_escape($vars{'LEXIMA_DMS_JWT_EXPIRES_MINUTES'}), '" size="10">';
print '</td></tr>';
print '</table>';

print '<h2>', $text{'lexima_dms_ldap'}, '</h2>';
print '<table>';
print '<tr><td>', $text{'lexima_dms_ldap_enabled'}, '</td><td>';
print '<input type="checkbox" name="LEXIMA_DMS_LDAP_ENABLED" value="1" ', ($vars{'LEXIMA_DMS_LDAP_ENABLED'} eq 'true' ? 'checked' : ''), '>';
print '</td></tr>';
print '<tr><td>', $text{'lexima_dms_ldap_url'}, '</td><td>';
print '<input type="text" name="LEXIMA_DMS_LDAP_URL" value="', quote_escape($vars{'LEXIMA_DMS_LDAP_URL'}), '" size="60">';
print '</td></tr>';
print '<tr><td>', $text{'lexima_dms_ldap_base_dn'}, '</td><td>';
print '<input type="text" name="LEXIMA_DMS_LDAP_BASE_DN" value="', quote_escape($vars{'LEXIMA_DMS_LDAP_BASE_DN'}), '" size="60">';
print '</td></tr>';
print '<tr><td>', $text{'lexima_dms_ldap_bind_dn'}, '</td><td>';
print '<input type="text" name="LEXIMA_DMS_LDAP_BIND_DN" value="', quote_escape($vars{'LEXIMA_DMS_LDAP_BIND_DN'}), '" size="60">';
print '</td></tr>';
print '<tr><td>', $text{'lexima_dms_ldap_bind_password'}, '</td><td>';
print '<input type="password" name="LEXIMA_DMS_LDAP_BIND_PASSWORD" value="', quote_escape($vars{'LEXIMA_DMS_LDAP_BIND_PASSWORD'}), '" size="40" autocomplete="off">';
print '</td></tr>';
print '<tr><td>', $text{'lexima_dms_ldap_user_search_filter'}, '</td><td>';
print '<input type="text" name="LEXIMA_DMS_LDAP_USER_SEARCH_FILTER" value="', quote_escape($vars{'LEXIMA_DMS_LDAP_USER_SEARCH_FILTER'}), '" size="60">';
print '</td></tr>';
print '<tr><td>', $text{'lexima_dms_ldap_user_dn_template'}, '</td><td>';
print '<input type="text" name="LEXIMA_DMS_LDAP_USER_DN_TEMPLATE" value="', quote_escape($vars{'LEXIMA_DMS_LDAP_USER_DN_TEMPLATE'}), '" size="60">';
print '</td></tr>';
print '<tr><td>', $text{'lexima_dms_ldap_default_role'}, '</td><td>';
print '<select name="LEXIMA_DMS_LDAP_DEFAULT_ROLE">';
for my $r (qw(author approver admin viewer)) {
    print '<option value="', $r, '"', ($vars{'LEXIMA_DMS_LDAP_DEFAULT_ROLE'} eq $r ? ' selected' : ''), '>', $r, '</option>';
}
print '</select>';
print '</td></tr>';
print '</table>';

print '<p><input type="submit" value="', $text{'lexima_dms_save'}, '"></p>';
print '</form>';

if ($in{'saved'}) {
    print '<p class="success">', $text{'lexima_dms_saved'}, '</p>';
}

sub quote_escape {
    my $s = shift || '';
    $s =~ s/&/&amp;/g;
    $s =~ s/</&lt;/g;
    $s =~ s/>/&gt;/g;
    $s =~ s/"/&quot;/g;
    return $s;
}

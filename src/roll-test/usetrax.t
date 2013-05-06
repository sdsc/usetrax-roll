#!/usr/bin/perl -w
# usetrax roll installation test.  Usage:
# usetrax.t [nodetype]
#   where nodetype is one of "Compute", "Dbnode", "Frontend" or "Login"
#   if not specified, the test assumes either Compute or Frontend

use Test::More qw(no_plan);

my $appliance = $#ARGV >= 0 ? $ARGV[0] :
                -d '/export/rocks/install' ? 'Frontend' : 'Compute';
my $installedOnAppliancesPattern = 'Frontend';
my $isInstalled = -d '/opt/usetrax';
my $output;

# usetrax-install.xml
if($appliance =~ /$installedOnAppliancesPattern/) {
  ok($isInstalled, 'usetrax installed');
} else {
  ok(! $isInstalled, 'usetrax not installed');
}

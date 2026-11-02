#!/usr/bin/perl

use strict;
use warnings;
# reading  from STDIN.
my $in = join '', <STDIN>;

#remove leangin and traing space;

$in =~ s/^\s+//;
$in =~ s/\s+$//;
$in =~ s/\s+/ /;

#return $in;

print ($in);

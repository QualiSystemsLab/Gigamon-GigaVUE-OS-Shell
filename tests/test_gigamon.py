#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for `GigamonDriver`
"""

import unittest

from driver import GigamonDriver

fakedata = {
    'terminal length 999': '',
    'enable': '',
    'configure terminal': '',
    'show version': '''Product name:      GigaVUE-OS
Product release:   4.6.02
Build ID:          #19704
Build date:        2016-05-19 04:34:43
Target arch:       ppc
Target hw:         gvcc2
Built by:          build_master@jenkins-slave055
Version summary:   GigaVUE-OS 4.6.02 #19704 2016-05-19 04:34:43 ppc gvcc2 build_master@jenkins-slave055:svn64243

U-Boot version:    2011.06-04610-gdb9d677-dirty.14
CPLD version:      df
TS version:        5456

Product model:     gvcc2
Product hw:        gvcc2
Host ID:           4b227abbb0e6

Uptime:            10d 0h 44m 23.872s
CPU load averages: 1.00 / 1.02 / 1.00
Number of CPUs:    4
System memory:     311 MB used / 3303 MB free / 3614 MB total
Swap:              0 MB used / 0 MB free / 0 MB total
''',
    'show version77': '''Product name:      GigaVUE-OS
Product release:   4.6.01.01
Build ID:          #19726
Build date:        2016-05-19 18:08:50
Target arch:       ppc
Target hw:         gvhc2
Built by:          build_master@jenkins-slave008
Version summary:   GigaVUE-OS 4.6.01.01 #19726 2016-05-19 18:08:50 ppc gvhc2 build_master@jenkins-slave008:svn64297

U-Boot version:    2011.06.6
CPLD version:      25
TS version:

Product model:     GigaVUE-HC2
Product hw:        gvhc2
Host ID:           5a13965639c8

Uptime:            25d 16h 50m 16.960s
CPU load averages: 1.04 / 1.04 / 1.02
Number of CPUs:    4
System memory:     235 MB used / 3379 MB free / 3614 MB total
Swap:              0 MB used / 0 MB free / 0 MB total


    ''',
    'show card': '''
Box ID: 1
Slot  Config  Oper Status        HW Type        Product Code  Serial Num  HW Rev
--------------------------------------------------------------------------------
1     yes     up           GigaPORT-Q02X32/32x  132-0087      1870-8103   B5-a2
2     yes     up           GigaPORT-Q02X32/32x  132-0087      1870-2157   B5-a2
cc1   yes     up           H-CCv2               132-0089      1890-1699   D0-df
4     yes     down         H-GigaSMART          132-00AD      1AD0-1584   B4-a2
''',
    'show chassis': '''
Chassis:
  Box ID            : 1*
  Hostname          : CSE-HD4-1
  Config            : yes
  Mode              : normal
  Oper Status       : up
  HW Type           : HD4-Chassis
  Vendor            : Gigamon
  Product Code      : 132-00A2
  Serial Num        : 41046
  HW Rev            : A11
  SW Rev            : 4.6.02

Backplane:
  HW type           : HD4-Backplane
  Product Code      : 132-00A1
  Serial Num        : 1A10-3317
  HW Rev            : A1

Fan Tray 1:
  HW type           : HD4-FAN-TRAY
  Product Code      : 132-00A3
  Serial Num        : 1A30-1401
  HW Rev            : B1
  Status            : on

Fan Tray 2:
  HW type           : HD4-FAN-TRAY
  Product Code      : 132-00A3
  Serial Num        : 1A30-1329
  HW Rev            : B1
  Status            : on

Power Module 1:
  HW type           : HD-Power-Supply-PDB
  Product Code      : 132-0049
  Serial Num        : 1490-1642
  HW Rev            : D0
  Status            : on

Power Module 2:
  HW type           : HD-Power-Supply-PDB
  Product Code      : 132-0049
  Serial Num        : 1490-1642
  HW Rev            : D0
  Status            : on
''',
    'show chassis6': '''

Chassis:
  Box ID            : -*
  Hostname          : GigaVUE-HD8
  Config            : -
  Mode              : -
  Oper Status       : up
  HW Type           : HD8-Chassis
  Vendor            : Gigamon
  Product Code      : 132-0098
  Serial Num        : 80035
  HW Rev            : A2
  SW Rev            : 4.7.00

Backplane:
  HW type           : HD8-Backplane
  Product Code      : 132-0043
  Serial Num        : 1430-0455
  HW Rev            : A0

Fan Tray:
  HW type           : HD8-FAN-TRAY
  Product Code      : 132-0044
  Serial Num        : 1440-0042
  HW Rev            : A1
  Status            : on

Power Module 1:
  HW type           : HD8-Power-Supply-PDB
  Product Code      : 132-0049
  Serial Num        : 1490-0093
  HW Rev            : A1
  Status            : on

Power Module 2:
  HW type           : HD8-Power-Supply-PDB
  Product Code      : 132-0049
  Serial Num        : 1490-0098
  HW Rev            : A1
  Status            : on

''',
    'show chassis2': '''
Chassis:
  Box ID            : 1*
  Hostname          : HC2-C01-35
  Config            : yes
  Mode              : normal
  Oper Status       : up
  HW Type           : HC2-Chassis
  Vendor            : Gigamon
  Product Code      : 132-00AZ
  Serial Num        : C0262
  HW Rev            : A4
  SW Rev            : 4.6.01.01

Backplane:
  HW type           : HC2-Mid-Plane
  Product Code      : 132-00AM
  Serial Num        : 1AM0-0173
  HW Rev            : A0

Fan Tray:
  HW type           : HC2-Fan-Tray
  Product Code      : 132-00B0
  Serial Num        : 1B00-012A
  HW Rev            : A0
  Status            : on

Power Module:
  HW type           : HC2-Power-Supply-PDB
  Product Code      : 132-00CH
  Serial Num        : 1CH0-0899
  HW Rev            : 1.0
  Status            : top=on bottom=on


Chassis:
  Box ID            : 2
  Hostname          : HC2-C01-35
  Config            : yes
  Mode              : normal
  Oper Status       : up
  HW Type           : HC2-Chassis
  Vendor            : Gigamon
  Product Code      : 132-00AZ
  Serial Num        : C0262-emubnaoebnubhaoe
  HW Rev            : A4
  SW Rev            : 4.6.01.01

Backplane:
  HW type           : HC2-Mid-Plane
  Product Code      : 132-00AM
  Serial Num        : 1AM0-0173
  HW Rev            : A0

Fan Tray:
  HW type           : HC2-Fan-Tray
  Product Code      : 132-00B0
  Serial Num        : 1B00-012A
  HW Rev            : A0
  Status            : on

Power Module:
  HW type           : HC2-Power-Supply-PDB
  Product Code      : 132-00CH
  Serial Num        : 1CH0-0899
  HW Rev            : 1.0
  Status            : top=on bottom=on
    ''',
    'show card7': '''
Box ID: Not configured
Slot  Config  Oper Status      HW Type      Product Code  Serial Num  HW Rev
----------------------------------------------------------------------------
1     no      inserted     H-GigaSMART      132-00AD      1AD0-0009   A3-a2
2     no      inserted     GigaPORT-X12G04  132-0045      1450-0218   C2-a6
3     no      inserted     GigaPORT-X04G44  132-0046      1460-0226   E1-a2
4     no      inserted     GigaPORT-Q02X32  132-0087      1870-0183   B2-a2
cc1   no      inserted     H-CCv2           132-0089      1890-1482   D0-df
cc2   no      inserted     H-CCv2           132-0089      1890-1423   D0
5     no      down         H-GigaSMART      132-00AD      1AD0-0030   A3-a2
6     no      inserted     GigaPORT-X12G04  132-0045      1450-0256   C2-a6
7     no      inserted     GigaPORT-X12G04  132-0045      1450-0192   C2-a6
8     no      inserted     GigaPORT-X12G04  132-0045      1450-0255   C2-a6

''',
    'show card77': '''
Box ID: 1
Slot  Config  Oper Status      HW Type     Product Code  Serial Num  HW Rev
---------------------------------------------------------------------------
cc1   yes     up           HC2-Main-Board  132-00AN      1AN0-00CB   B1-25
1     yes     up           PRT-HC0-X24     132-00BD      1BD0-0189   A1-a2
2     yes     up           BPS-HC0-D25A4G  132-00BQ      1BQ0-002E   2.1-1
3     yes     up           BPS-HC0-D25B4G  132-00BF      1BF0-0638   A2-1
4     yes     mismatch     SMT-HC0-X16     132-00BK      1BD0-0024   2.2-a2
5     yes     up           SMT-HC0-R       132-00AT      1AT0-0158   A0-5

# fake:
Box ID: 2
Slot  Config  Oper Status      HW Type     Product Code  Serial Num  HW Rev
---------------------------------------------------------------------------
cc2   yes     up           HC2-Main-Board  132-00AN      1AN0-00CB   B1-25
6     yes     up           PRT-HC0-X24     132-00BD      1BD0-0189   A1-a2
7     yes     up           BPS-HC0-D25A4G  132-00BQ      1BQ0-002E   2.1-1
8     yes     up           BPS-HC0-D25B4G  132-00BF      1BF0-0638   A2-1
9     yes     mismatch     SMT-HC0-X16     132-00BK      1BD0-0024   2.2-a2
10     yes     up           SMT-HC0-R       132-00AT      1AT0-0158   A0-5


    ''',
    'show port4': '''


===============================================================================================================================================

                                                Link    Xcvr Pwr (dBm)  Pwr       Xcvr         Auto                      Force  Port

Port      Type        Alias        Admin        Status  (min     max )  THld      Type         Neg        Speed  Duplex  LnkUp  Relay    Dscvry

-----------------------------------------------------------------------------------------------------------------------------------------------

1/1/x1    hybrid      -            enabled      up               -4.94            sfp sx       off         1000  full    off    N/A      off

1/1/x2    hybrid      -            enabled      up               -5.07            sfp sx       off         1000  full    off    N/A      off

1/1/x3    hybrid      -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x4    hybrid      -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x5    network     -            enabled      up               -5.23            sfp sx       off         1000  full    off    N/A      off

1/1/x6    tool        -            disabled     -               -26.20  --        sfp sx       off            -  -       off    N/A      off

1/1/x7    tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x8    tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x9    tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x10   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x11   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x12   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x13   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x14   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x15   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x16   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x17   network     Ostinat...   enabled      up                   -            sfp cu       on          1000  full    off    N/A      off

1/1/x18   tool        WireSha...   enabled      up                   -            sfp cu       on          1000  full    off    N/A      off

1/1/x19   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x20   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x21   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x22   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x23   hybrid      -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x24   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x25   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x26   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x27   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x28   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/1/x29   tool        To-HC2-...   enabled      up               -2.17            sfp+ sr      off        10000  full    off    N/A      off

1/1/x30   tool        To-HC2-...   enabled      up               -3.92            sfp+ sr      off        10000  full    off    N/A      off

1/1/x31   tool        To-HC2-...   enabled      up               -2.23            sfp+ sr      off        10000  full    off    N/A      off

1/1/x32   tool        To-HC2-...   enabled      up               -2.15            sfp+ sr      off        10000  full    off    N/A      off

1/2/x1    network     -            disabled     -               -29.21  --        sfp sx       off            -  -       off    N/A      off

1/2/x2    network     -            disabled     -               -26.78  --        sfp sx       off            -  -       off    N/A      off

1/2/x3    network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x4    network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x5    network     -            disabled     -               -27.96  --        sfp sx       off            -  -       off    N/A      off

1/2/x6    network     -            disabled     -               -24.44  --        sfp sx       off            -  -       off    N/A      off

1/2/x7    network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x8    network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x9    network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x10   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x11   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x12   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x13   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x14   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x15   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x16   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x17   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x18   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x19   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x20   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x21   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x22   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x23   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x24   network     -            disabled     -                    -            none         off            -  -       off    N/A      off

1/2/x25   tool        To-HC2-...   enabled      up               -5.14            sfp sx       off         1000  full    off    N/A      off

1/2/x26   tool        To-HC2-...   enabled      up               -4.80            sfp sx       off         1000  full    off    N/A      off

1/2/x27   tool        To-HC2-...   enabled      up               -4.55            sfp sx       off         1000  full    off    N/A      off

1/2/x28   tool        To-HC2-...   enabled      up               -4.53            sfp sx       off         1000  full    off    N/A      off

1/2/x29   network     -            enabled      up               -5.60            sfp sx       off         1000  full    off    N/A      off

1/2/x30   network     -            enabled      up               -5.85            sfp sx       off         1000  full    off    N/A      off

1/2/x31   network     -            enabled      up               -4.97            sfp sx       off         1000  full    off    N/A      off

1/2/x32   network     -            enabled      up               -5.17            sfp sx       off         1000  full    off    N/A      off

1/4/e1    gs          N/A          enabled      down                 -            N/A          N/A        40000  full    off    N/A

1/4/e2    gs          N/A          enabled      up                   -            N/A          N/A        40000  full    off    N/A

-----------------------------------------------------------------------------------------------------------------------------------------------



Legend : Power THld :  ++ High Alarm    + High Alert    -- Low Alarm    - Low Alert


''',
    'show port0': '''% There is no chassis configured.
''',
    'show port7': '''HB1-C01-38 # show port
========================================================================================================================
                                 Link    Xcvr Pwr (dBm)  Pwr   Xcvr         Auto                  Force  Port
Port      Type         Admin     Status  (min     max )  THld  Type         Neg    Speed  Duplex  LnkUp  Relay    Dscvry
------------------------------------------------------------------------------------------------------------------------
1/1/e1    gs           enabled   up                   -        N/A          N/A    10000  full    off    N/A
1/1/g1    network      disabled  -                    -        COPPER       on         -  -       off    N/A      off
1/1/g2    network      disabled  -                    -        COPPER       on         -  -       off    N/A      off
1/1/g3    network      disabled  -                    -        COPPER       on         -  -       off    N/A      off
1/1/g4    network      disabled  -                    -        COPPER       on         -  -       off    N/A      off
1/1/g5    network      disabled  -                    -        COPPER       on         -  -       off    N/A      off
1/1/g6    network      disabled  -                    -        COPPER       on         -  -       off    N/A      off
1/1/g7    network      disabled  -                    -        COPPER       on         -  -       off    N/A      off
1/1/g8    network      disabled  -                    -        COPPER       on         -  -       off    N/A      off
1/1/g9    network      disabled  -                    -        none         on         -  -       off    N/A      off
1/1/g10   network      disabled  -                    -        none         on         -  -       off    N/A      off
1/1/g11   network      disabled  -                    -        none         on         -  -       off    N/A      off
1/1/g12   network      disabled  -                    -        none         on         -  -       off    N/A      off
1/1/g13   network      disabled  -                    -        none         on         -  -       off    N/A      off
1/1/g14   network      disabled  -                    -        none         on         -  -       off    N/A      off
1/1/g15   network      disabled  -                    -        none         on         -  -       off    N/A      off
1/1/g16   network      disabled  -                    -        none         on         -  -       off    N/A      off
1/1/x1    network      disabled  -                    -        none         off        -  -       off    N/A      off
1/1/x2    network      disabled  -                    -        none         off        -  -       off    N/A      off
1/1/x3    network      disabled  -                    -        none         off        -  -       off    N/A      off
1/1/x4    network      disabled  -                    -        none         off        -  -       off    N/A      off
------------------------------------------------------------------------------------------------------------------------

Legend : Power THld :  ++ High Alarm    + High Alert    -- Low Alarm    - Low Alert


HB1-C01-38 #
''',
    'show port alias': '''=========================================================================================
Port       Type     Aliases
-----------------------------------------------------------------------------------------
1/1/x17    network  Ostinato-Traff-Gen-Tool
1/1/x18    tool     WireShark-Tool
1/1/x29    tool     To-HC2-3_bid5-slot2-x1
1/1/x30    tool     To-HC2-3_bid5-slot2-x2
1/1/x31    tool     To-HC2-3_bid5-slot2-x3
1/1/x32    tool     To-HC2-3_bid5-slot2-x4
1/2/x25    tool     To-HC2-1_bid3-slot4-x9
1/2/x26    tool     To-HC2-1_bid3-slot4-x10
1/2/x27    tool     To-HC2-1_bid3-slot4-x11
1/2/x28    tool     To-HC2-1_bid3-slot4-x12
-----------------------------------------------------------------------------------------
''',
    'show port': '''===============================================================================================================================================
                                                Link    Xcvr Pwr (dBm)  Pwr       Xcvr         Auto                      Force  Port
Port      Type        Alias        Admin        Status  (min     max )  THld      Type         Neg        Speed  Duplex  LnkUp  Relay    Dscvry
-----------------------------------------------------------------------------------------------------------------------------------------------
1/1/x1    hybrid      -            enabled      up               -4.94            sfp sx       off         1000  full    off    N/A      off
1/1/x2    hybrid      -            enabled      up               -5.08            sfp sx       off         1000  full    off    N/A      off
1/1/x3    hybrid      -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x4    hybrid      -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x5    network     -            enabled      up               -5.22            sfp sx       off         1000  full    off    N/A      off
1/1/x6    tool        -            disabled     -               -26.20  --        sfp sx       off            -  -       off    N/A      off
1/1/x7    tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x8    tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x9    tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x10   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x11   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x12   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x13   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x14   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x15   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x16   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x17   network     Ostinat...   enabled      up                   -            sfp cu       on          1000  full    off    N/A      off
1/1/x18   tool        WireSha...   enabled      up                   -            sfp cu       on          1000  full    off    N/A      off
1/1/x19   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x20   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x21   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x22   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x23   hybrid      -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x24   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x25   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x26   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x27   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x28   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x29   tool        To-HC2-...   enabled      up               -2.27            sfp+ sr      off        10000  full    off    N/A      off
1/1/x30   tool        To-HC2-...   enabled      up               -3.92            sfp+ sr      off        10000  full    off    N/A      off
1/1/x31   tool        To-HC2-...   enabled      up               -2.22            sfp+ sr      off        10000  full    off    N/A      off
1/1/x32   tool        To-HC2-...   enabled      up               -2.15            sfp+ sr      off        10000  full    off    N/A      off
1/2/x1    network     -            disabled     -               -29.21  --        sfp sx       off            -  -       off    N/A      off
1/2/x2    network     -            disabled     -               -26.78  --        sfp sx       off            -  -       off    N/A      off
1/2/x3    network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x4    network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x5    network     -            disabled     -               -27.96  --        sfp sx       off            -  -       off    N/A      off
1/2/x6    network     -            disabled     -               -24.44  --        sfp sx       off            -  -       off    N/A      off
1/2/x7    network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x8    network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x9    network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x10   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x11   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x12   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x13   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x14   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x15   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x16   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x17   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x18   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x19   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x20   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x21   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x22   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x23   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x24   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x25   tool        To-HC2-...   enabled      up               -5.13            sfp sx       off         1000  full    off    N/A      off
1/2/x26   tool        To-HC2-...   enabled      up               -4.72            sfp sx       off         1000  full    off    N/A      off
1/2/x27   tool        To-HC2-...   enabled      up               -4.55            sfp sx       off         1000  full    off    N/A      off
1/2/x28   tool        To-HC2-...   enabled      up               -4.52            sfp sx       off         1000  full    off    N/A      off
1/2/x29   network     -            enabled      up               -5.61            sfp sx       off         1000  full    off    N/A      off
1/2/x30   network     -            enabled      up               -5.84            sfp sx       off         1000  full    off    N/A      off
1/2/x31   network     -            enabled      up               -4.98            sfp sx       off         1000  full    off    N/A      off
1/2/x32   network     -            enabled      up               -5.18            sfp sx       off         1000  full    off    N/A      off
1/4/e1    gs          N/A          enabled      down                 -            N/A          N/A        40000  full    off    N/A
1/4/e2    gs          N/A          enabled      up                   -            N/A          N/A        40000  full    off    N/A
-----------------------------------------------------------------------------------------------------------------------------------------------

Legend : Power THld :  ++ High Alarm    + High Alert    -- Low Alarm    - Low Alert

''',
    'show port2': '''
HC2-C01-35 # show port
===============================================================================================================================================
                                                Link    Xcvr Pwr (dBm)  Pwr       Xcvr         Auto                      Force  Port
Port      Type        Alias        Admin        Status  (min     max )  THld      Type         Neg        Speed  Duplex  LnkUp  Relay    Dscvry
-----------------------------------------------------------------------------------------------------------------------------------------------
1/1/x1    network     CoreSpan1    enabled      down            -40.00  --        sfp+ sr      off        10000  full    off    N/A      off
1/1/x2    tool        OutOfBa...   enabled      down            -40.00  --        sfp+ sr      off        10000  full    off    N/A      off
1/1/x3    tool        SIEM         enabled      down            -30.00  --        sfp+ sr      off        10000  full    off    N/A      off
1/1/x4    tool        RecordA...   enabled      down            -40.00  --        sfp+ sr      off        10000  full    off    N/A      off
1/1/x5    network     CoreSpan2    enabled      down             -4.88            sfp+ sr      off        10000  full    off    N/A      off
1/1/x6    hybrid      -            enabled      up               -2.20            sfp+ sr      off        10000  full    off    N/A      off
1/1/x7    hybrid      -            enabled      up               -4.88            sfp+ sr      off        10000  full    off    N/A      off
1/1/x8    network     -            disabled     -                -2.93            sfp+ sr      off            -  -       off    N/A      off
1/1/x9    tool        -            enabled      down            -33.98  --        sfp+ sr      off        10000  full    off    N/A      off
1/1/x10   tool        -            enabled      down            -36.99  --        sfp+ sr      off        10000  full    off    N/A      off
1/1/x11   tool        NewTool      disabled     -               -33.98  --        sfp+ sr      off            -  -       off    N/A      off
1/1/x12   network     Spirent...   enabled      down            -40.00  --        sfp+ sr      off        10000  full    off    N/A      off
1/1/x13   network     Tap2In       enabled      down            -40.00  --        sfp+ sr      off        10000  full    off    N/A      off
1/1/x14   network     Tap2Out      disabled     -               -40.00  --        sfp+ sr      off            -  -       off    N/A      off
1/1/x15   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x16   network     Tap1In       enabled      down                 -            none         off        10000  full    off    N/A      off
1/1/x17   network     Tap1Out      disabled     -                    -            none         off            -  -       off    N/A      off
1/1/x18   tool        -            enabled      down                 -            none         off        10000  full    off    N/A      off
1/1/x19   network     -            disabled     -                    -            sfp cu       on             -  -       off    N/A      off
1/1/x20   hybrid      -            enabled      up                   -            sfp cu       on          1000  full    off    N/A      off
1/1/x21   network     -            enabled      up                   -            sfp cu       on          1000  full    off    N/A      off
1/1/x22   tool        -            enabled      up                   -            sfp cu       on          1000  full    off    N/A      off
1/1/x23   network     AccessS...   enabled      up                   -            sfp cu       on          1000  full    off    N/A      off
1/1/x24   tool        Wiresha...   enabled      up                   -            sfp cu       on          1000  full    off    N/A      off
1/2/x1    network     -            disabled     -                -2.58            sfp+ sr      off            -  -       off    N/A      off
1/2/x2    network     -            disabled     -                -2.75            sfp+ sr      off            -  -       off    N/A      off
1/2/x3    inline-net  -            enabled      up               -2.57            sfp+ sr      off        10000  full    off    N/A      off
1/2/x4    inline-net  -            enabled      up               -7.28            sfp+ sr      off        10000  full    off    N/A      off
1/2/x5    inline-tool  -            enabled      down                 -            none         off        10000  full    off    N/A      off
1/2/x6    inline-tool  -            enabled      down                 -            none         off        10000  full    off    N/A      off
1/2/x7    inline-tool  -            enabled      down                 -            none         off        10000  full    off    N/A      off
1/2/x8    inline-tool  -            enabled      down                 -            none         off        10000  full    off    N/A      off
1/2/x9    inline-tool  -            enabled      down                 -            sfp cu       on          1000  full    off    N/A      off
1/2/x10   inline-tool  -            enabled      down                 -            sfp cu       on          1000  full    off    N/A      off
1/2/x11   inline-tool  -            enabled      down                 -            none         off        10000  full    off    N/A      off
1/2/x12   inline-tool  -            enabled      down                 -            none         off        10000  full    off    N/A      off
1/2/x13   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x14   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x15   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x16   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/2/x17   inline-net  -            enabled      down            -30.97  --        bps sx/sr    off        10000  full    off    N/A      off
1/2/x18   inline-net  -            enabled      down            -29.59  --        bps sx/sr    off        10000  full    off    N/A      off
1/2/x19   inline-net  -            disabled     -               -40.00  --        bps sx/sr    off            -  -       off    N/A      off
1/2/x20   inline-net  -            disabled     -               -36.99  --        bps sx/sr    off            -  -       off    N/A      off
1/2/x21   inline-net  -            disabled     -               -36.99  --        bps sx/sr    off            -  -       off    N/A      off
1/2/x22   inline-net  -            disabled     -               -40.00  --        bps sx/sr    off            -  -       off    N/A      off
1/2/x23   inline-net  -            disabled     -               -40.00  --        bps sx/sr    off            -  -       off    N/A      off
1/2/x24   inline-net  -            disabled     -               -40.00  --        bps sx/sr    off            -  -       off    N/A      off
1/3/x1    tool        -            enabled      up               -2.86            sfp+ sr      off        10000  full    off    N/A      off
1/3/x2    hybrid      -            enabled      up               -2.62            sfp+ sr      off        10000  full    off    N/A      off
1/3/x3    hybrid      -            enabled      up               -2.69            sfp+ sr      off        10000  full    off    N/A      off
1/3/x4    network     -            disabled     -                -2.29            sfp+ sr      off            -  -       off    N/A      off
1/3/x5    network     -            disabled     -               -35.23  --        sfp+ sr      off            -  -       off    N/A      off
1/3/x6    network     -            disabled     -               -40.00  --        sfp+ sr      off            -  -       off    N/A      off
1/3/x7    network     -            disabled     -               -40.00  --        sfp+ sr      off            -  -       off    N/A      off
1/3/x8    network     -            disabled     -               -40.00  --        sfp+ sr      off            -  -       off    N/A      off
1/3/x9    network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/3/x10   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/3/x11   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/3/x12   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/3/x13   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/3/x14   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/3/x15   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/3/x16   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/3/x17   inline-net  -            disabled     -               -35.23  --        bps sx/sr    off            -  -       off    N/A      off
1/3/x18   inline-net  -            disabled     -               -35.23  --        bps sx/sr    off            -  -       off    N/A      off
1/3/x19   inline-net  -            disabled     -               -40.00  --        bps sx/sr    off            -  -       off    N/A      off
1/3/x20   inline-net  -            disabled     -               -40.00  --        bps sx/sr    off            -  -       off    N/A      off
1/3/x21   inline-net  -            disabled     -               -40.00  --        bps sx/sr    off            -  -       off    N/A      off
1/3/x22   inline-net  -            disabled     -               -36.99  --        bps sx/sr    off            -  -       off    N/A      off
1/3/x23   inline-net  -            disabled     -               -33.01  --        bps sx/sr    off            -  -       off    N/A      off
1/3/x24   inline-net  -            disabled     -               -40.00  --        bps sx/sr    off            -  -       off    N/A      off
1/4/e1    gs          N/A          enabled      down                 -            N/A          N/A        40000  full    off    N/A
1/4/x1    tool        -            enabled      down                 -            none         on         10000  full    off    N/A      off
1/4/x2    hybrid      -            enabled      up                   -            none         on         10000  full    off    N/A      off
1/4/x3    network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/4/x4    network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/4/x5    network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/4/x6    network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/4/x7    network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/4/x8    network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/4/x9    network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/4/x10   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/4/x11   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/4/x12   tool        -            disabled     -                    -            none         off            -  -       off    N/A      off
1/4/x13   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/4/x14   network     -            disabled     -                    -            none         off            -  -       off    N/A      off
1/4/x15   inline-tool  -            disabled     -                    -            none         off            -  -       off    N/A      off
1/4/x16   inline-tool  -            disabled     -                    -            none         off            -  -       off    N/A      off
1/5/e1    gs          N/A          enabled      up                   -            N/A          N/A        40000  full    off    N/A
-----------------------------------------------------------------------------------------------------------------------------------------------

Legend : Power THld :  ++ High Alarm    + High Alert    -- Low Alarm    - Low Alert



    '''
}

d = GigamonDriver()
d.fakedata = fakedata

inv = d.get_inventory(None)

print 'Resources:'
for res in inv.resources:
    print '%s %s %s' % (res.model, res.name, res.relative_address)

print 'Attributes:'
for attr in inv.attributes:
    print '%s: %s = %s' % (attr.relative_address, attr.attribute_name, attr.attribute_value)
print 'End'
#
# savefolders = [
#     'ftp://user:password@server/a/b/c',
#     'tftp://server/a/b/c',
#     'server/a/b/c',
#     'c',
# ]
#
# savedfiles = []
#
# for savefolder in savefolders:
#     savedfiles.append(d.save(None, None, 'running', savefolder, 'vrf'))
#     try:
#         savedfiles.append(d.save(None, None, 'startup', savefolder, 'vrf'))
#     except:
#         print 'Got expected exception'
#
#
# for savedfile in savedfiles:
#     d.restore(None, None, savedfile, 'override', 'running', 'vrf')
#     try:
#         d.restore(None, None, savedfile, 'append', 'running', 'vrf')
#     except:
#         print 'Got expected exception'
#
# firmware_path_host = [
#     ('a/b/c', 'host'),
#     ('ftp://user:password@server/a/b/c/f.bin', ''),
#     ('tftp://server/a/b/c/g.bin', ''),
# ]
#
# for path, host in firmware_path_host:
#     d.load_firmware(None, None, path, host)

# class TestGigamonDriver(unittest.TestCase):
#
#     def setUp(self):
#         pass
#
#     def tearDown(self):
#         pass
#
#     def test_000_something(self):
#         pass
#
#
# if __name__ == '__main__':
#     import sys
#     sys.exit(unittest.main())

#include <algorithm>
#include <vector>

#ifdef Q_OS_LINUX
#include <syslog.h>
#else
#include <iostream>
#endif

int calcula_else(int a, int b) {
    return a - b;
}

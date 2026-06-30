#include <algorithm>
#include <vector>

#ifdef Q_OS_LINUX
#include <syslog.h>
using fake::logging::FakeQtLogging;
#endif

int faz_algo(int a, int b) {
    return a + b;
}

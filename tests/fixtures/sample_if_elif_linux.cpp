#include <algorithm>
#include <vector>

#if defined(Q_OS_WIN)
#include <windows.h>
#elif defined(Q_OS_LINUX)
#include <syslog.h>
using odin::logging::OdinQTLogging;
#endif

int calcula_linux(int a, int b) {
    return a + b;
}

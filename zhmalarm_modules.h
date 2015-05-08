#include <stdint.h>
typedef void (*monitoralarm_func)(int name, void *user_data);
void zhm_monitoralarm(monitoralarm_func user_func, void *user_data);
void zhm_cleanup(void);
// void zhm_sendchar(char s);


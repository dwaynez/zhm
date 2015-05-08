/*
 * Copyright (C) Dwayne Zon 2015 <dwayne.zon@gmail.com> 
 * 
 * This program is free software; you can redistribute it and/or modify
 *   it under the terms of the GNU General Public License as published
 *   by the Free Software Foundation
 */

#include "zhmalarm_modules.h"
#include <pigpio.h>
#include <pthread.h>
#include <unistd.h> // For sleep function
#include <stdio.h>  // For printf
#include <signal.h> // debug signal 11 error
#include <string.h> // for strlen function
 
typedef void (*monitoralarm_func)(int name, void *user_data);
static int keypad, panel, prevcode = 0, prealarm = 0;
static uint32_t g_mask, data_mask, clock_mask;
static uint32_t prevtick = 0;
static int armed;
static int bit = 17;
static int savedcode = 0;
static int stoploop;
static pthread_mutex_t mutex = PTHREAD_MUTEX_INITIALIZER;
//~ static pthread_mutex_t mutex2 = PTHREAD_MUTEX_INITIALIZER;
/*
 * Trap segment fault - debug
 */
 void sighandler(int signum)
{
    printf("Process %d got signal %d\n", getpid(), signum);
    signal(signum, SIG_DFL);
    kill(getpid(), signum);
}
/*
 * Set code in a thread safe manner
 */
int set_code(int newcode)
{
	pthread_mutex_lock(&mutex);
	int prevcode;
	prevcode = savedcode;
	savedcode = newcode;
	pthread_mutex_unlock(&mutex);
 	return prevcode;
}

/*
 * Do nothing - function required so gpgio 23 is reported in samples
 */
void donothing(int gpio, int level, uint32_t tick)
{
// do nothing   
    //~ printf("do nothing gpio %d became %d at %d\n", gpio, level, tick);
    //~ printf("donothing. tick=%d\n",tick);


}

/*
 * Clockpulse - function triggered by a clock pulse - see if data neeeds to be sent
void clockpulse(int gpio, int level, uint32_t tick)
{
    if (strlen(outputbuffer) > 0) {
        if (prevclocktick == 0)
            prevclocktick = tick;
        //~ printf("Clockpulse. Clock bit=%d. level=%d tick=%d. Diff=%d\n",clockbit, level, tick, tick - prevclocktick);
    
        if ((level == 0) && (tick - prevclocktick > 1000)) {
            //~ printf("start cycle clockbit=%d\n",clockbit);
            dumpbits = 1;
            if ((clockbit != 0) && (clockbit != 9)) {
                printf("Incomplete clocking. Clock bit=%d. Resending=%x. Diff=%d\n",clockbit,outputbuffer[outputptr], tick - prevclocktick);
            }
            clockbit = 0;
        } else if (level == 1) {
            //~ printf("clockbit=%d\n",clockbit);
            if (clockbit < 8) {
                if ((outputmask & outputbuffer[outputptr]) > 0) {
                    gpioWrite(25, 0);
                    //~ printf("25 set low %d\n",bit);
                    printf("Clockpulse. tick=%d\n",tick);

                } else {
                    gpioWrite(25, 1);
                    //~ printf("25 set high %d\n",bit);
                }
                outputmask >>= 1;
                clockbit++;
            } else if (clockbit == 8) {
                gpioWrite(25, 1);
                    //~ printf("25 set high finally %d\n",bit);
                clockbit++;
            } else {
                outputmask = 0x40;
                outputbuffer[outputptr] = '\0';
                if (outputbuffer[outputptr+1] == '\0')
                    outputptr = 0;
                else
                    outputptr++;
            }
		}
	}
    prevclocktick = tick;

}
 */

/*
 * Call back routine to process alarm pulses
 */
void ProcessAlarmData(const gpioSample_t *samples, int numSamples)
{
	static uint32_t state = 0;
	uint32_t low, level;
	int s, code;
    //~ int tt_s;
	int difftick, databit;
//	printf("numsamples=%d\n",numSamples);
                        	//~ printf("panel=%d\n", panel);

						//~ set_code(255);  //debug
// printf("panel referencced\n");
    //~ if (tempdelaycount == 0) {  printf("processalarmdata called\n"); tempdelaycount ++; }
        
	for (s=0; s<numSamples; s++)
        {
		if (prevtick == 0)
			prevtick = samples[0].tick;
		level = samples[s].level;
		low = ((state ^ level) & clock_mask) & ~level;
		state = level;
        
        //~ if ((dumpbits == 1) || (strlen(outputbuffer) > 0))
            //~ printf("bit=%d, Nevel=%x, low=%d, tick=%d, tickdiff=%d\n",bit, samples[s].level, low, samples[s].tick, samples[s].tick-samples[s-1].tick);

		if (low) {
            if (s == 0)
                difftick = samples[s].tick - prevtick;
            else
                difftick = samples[s].tick - samples[s-1].tick;
            databit = (level & data_mask) == 0;
                   // printf ("keypad= %d; panel= %d\n",keypad,panel);
        //		printf("bid =%d, tick= %d. low=%d databit=%d data=%d\n", bit, difftick, low, (databit),(level & data_mask));
            // Start of a data send - after a long high, 8 low pulses, followed by a 400ms gap and then 8 more pulses 
            //  - if starting a new one, dump the previous one
            if (difftick > 1000) {
                if (bit == 16) {
                    //~ if (keypad > 0) printf("keypad= %x\n",keypad);
                    code = prevcode;
                    if (armed == 1) {
                        if (panel == 0) {
                            armed = 0;
                            code = 0;
                            prealarm = 0;
                            //~ if (prepanel != panel) {
								//~ printf("alarm turned off\n");
								//~ prepanel = panel;
							//~ }
                        } else if (panel > 0x7F) {
                            //~ if (prepanel != panel) {
								//~ printf("prealarm set code = %d\n",panel);
								//~ prepanel = panel;
							//~ }
							prealarm = 1;
						} else if ((panel < 0x7F) && (prealarm == 0)) {
							//~ if (prepanel != panel) {
								//~ printf("alarm set code = %d\n",panel);
								//~ prepanel = panel;
							//~ }
                            code = 0x7F - panel + 0x80;
						} else if ((panel == 0x7F) && (prealarm == 1)) {
							prealarm = 0;
						}
                    } else if (panel == 0x7F) {
                        armed = 1;
							//~ if (prepanel != panel) {
								//~ printf("alarm turned on code = %d\n",panel);
								//~ prepanel = panel;
							//~ }
                        code = 0x80;
                    }
                    if (prevcode != code) {
                        //~ printf("calling setcode=%d\n",code);
						set_code(code);
                        prevcode = code;
                    }
                    //~ else if (keypad > 0) set_code(keypad);

                }
                //~ else printf("Incomplete\n");
                keypad = 0;
                panel = 0;
                bit = 0;
                }
            if (bit < 8) {
                keypad = keypad << 1;
                keypad += databit;
                //~ if (databit > 0)
                    //~ if (dumpbits == 0) {
                        //~ dumpbits = 1;
                        //~ for (tt_s=1; tt_s<=s; tt_s++)
                            //~ printf("s=%d Level=%x,tickdiff=%d\n",tt_s,samples[tt_s].level, samples[tt_s].tick-samples[tt_s-1].tick);
                    //~ }
                }
            else {
                //~ dumpbits = 0;
                //~ if (keypad > 0) printf("bit=%d. keypad=%x\n",bit, keypad);
                panel = panel << 1;
                panel += databit;
                } 
            bit += 1;
            }
        }
    prevtick = samples[numSamples-1].tick;
}
void zhm_monitoralarm(monitoralarm_func user_func, void *user_data) {
	int newcode;
	signal(SIGSEGV, sighandler);
	//~ pthread_mutex_init(&mutex);
    keypad = 0;
    panel = 0;
//~ printf("zhm monitor alarm initialized 1\n");
    bit = 0;
    armed = 0;
    prevcode = 256;
    //~ outputbuffer[0] = '\0';
    stoploop = 0;
    //~ sleep(10);
	//~ user_func(128, user_data);  //debug
	//~ sleep(10);
    if (gpioInitialise()>=0)  { 
		clock_mask |= (1<<24);
		data_mask |= (1<<23);
		g_mask = clock_mask;
		gpioSetAlertFunc(23, donothing);
		//~ gpioSetAlertFunc(24, clockpulse);
		gpioSetGetSamplesFunc(ProcessAlarmData, g_mask);
		gpioSetMode(24, PI_INPUT);
		gpioSetMode(23, PI_INPUT);
		//~ gpioSetMode(25, PI_OUTPUT);
		//~ gpioWrite(25, 1);

		newcode = 111;
		while (stoploop == 0) {
			newcode = set_code(256);
			if (newcode != 256) {
				user_func(newcode, user_data);  //debug
			}
			sleep(5);
		}
		gpioTerminate();
	} else
		printf("GPIO initialise failed\n");
}

/*
 * Add character to be sent to buffer
 */
//~ void zhm_sendchar(char s) {
    //~ int l;
	//~ pthread_mutex_lock(&mutex2);
    //~ l = strlen(outputbuffer);
    //~ outputbuffer[l] = s;
    //~ outputbuffer[l+1] = '\0';
	//~ pthread_mutex_unlock(&mutex2);
//~ }

/*
 * Cleanup and sutdown
 */
void zhm_cleanup(void) {
	//~ printf("cleanup called");
	stoploop = 1;
}

#ifndef BUFFER_H
#define BUFFER_H

#define _GNU_SOURCE
#include <stddef.h>

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <sys/ipc.h>
#include <sys/shm.h>
#include <semaphore.h>
#include <fcntl.h>
#include <string.h>
#include <time.h>

#define BUFFER_SIZE 10
#define SHM_KEY 0x1234
#define SEM_MUTEX "/sem_mutex"
#define SEM_EMPTY "/sem_empty"
#define SEM_FULL "/sem_full"

typedef struct {
   int value;
   int producer_id;
} item_t;

typedef struct {
   item_t buffer[BUFFER_SIZE];
   int head;
   int tail;
   int count;
} shared_buffer_t;

#endif

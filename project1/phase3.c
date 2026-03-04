#include <pthread.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <time.h>
#include <string.h>

#define NUM_ACCOUNTS 2
#define INITIAL_BALANCE 1000.0

typedef struct {
    int account_id;
    double balance;
    int transaction_count;
    pthread_mutex_t lock;
} Account;

Account accounts[NUM_ACCOUNTS];

pthread_barrier_t start_barrier;

pthread_mutex_t progress_lock = PTHREAD_MUTEX_INITIALIZER;
time_t last_progress_time;

void initialize_accounts() {
    for (int i = 0; i < NUM_ACCOUNTS; i++) {
        accounts[i].account_id = i;
        accounts[i].balance = INITIAL_BALANCE;
        accounts[i].transaction_count = 0;
        pthread_mutex_init(&accounts[i].lock, NULL);
    }
}

void cleanup_mutexes() {
    for (int i = 0; i < NUM_ACCOUNTS; i++) {
        pthread_mutex_destroy(&accounts[i].lock);
    }
    pthread_mutex_destroy(&progress_lock);
    pthread_barrier_destroy(&start_barrier);
}

void transfer_deadlock(int from_id, int to_id, double amount) {

    pthread_mutex_lock(&accounts[from_id].lock);
    printf("Thread %lu locked account %d\n", (unsigned long)pthread_self(), from_id);

    usleep(100000);

    printf("Thread %lu waiting for account %d\n", (unsigned long)pthread_self(), to_id);
    pthread_mutex_lock(&accounts[to_id].lock);

    if (accounts[from_id].balance >= amount) {
        accounts[from_id].balance -= amount;
        accounts[to_id].balance += amount;
        accounts[from_id].transaction_count++;
        accounts[to_id].transaction_count++;

        printf("Thread %lu transferred %.2f from %d to %d\n",
               (unsigned long)pthread_self(), amount, from_id, to_id);

        pthread_mutex_lock(&progress_lock);
        last_progress_time = time(NULL);
        pthread_mutex_unlock(&progress_lock);
    }

    pthread_mutex_unlock(&accounts[to_id].lock);
    pthread_mutex_unlock(&accounts[from_id].lock);
}

typedef struct {
    int from;
    int to;
    double amount;
} TransferArgs;

void* transfer_thread(void* arg) {
    TransferArgs* t = (TransferArgs*)arg;

    pthread_barrier_wait(&start_barrier);

    transfer_deadlock(t->from, t->to, t->amount);

    return NULL;
}

int main() {

    printf("=== Phase 3: Deadlock Creation ===\n");

    initialize_accounts();

    pthread_barrier_init(&start_barrier, NULL, 2);

    pthread_mutex_lock(&progress_lock);
    last_progress_time = time(NULL);
    pthread_mutex_unlock(&progress_lock);

    pthread_t t1, t2;

    TransferArgs a1 = {0, 1, 100.0};
    TransferArgs a2 = {1, 0, 100.0};

   	 int rc1 = pthread_create(&t1, NULL, transfer_thread, &a1);
	if (rc1 != 0) {
    fprintf(stderr, "pthread_create failed (code %d)\n", rc1);
    exit(1);
	}

	int rc2 = pthread_create(&t2, NULL, transfer_thread, &a2);
	if (rc2 != 0) {
    fprintf(stderr, "pthread_create failed (code %d)\n", rc2);
    exit(1);
	}

    while (1) {

        sleep(1);

        pthread_mutex_lock(&progress_lock);
        time_t now = time(NULL);
        time_t diff = now - last_progress_time;
        pthread_mutex_unlock(&progress_lock);

        if (diff >= 5) {

            printf("\nSuspected deadlock detected\n");
            printf("No completed transfer progress for %ld seconds\n", (long)diff);
            printf("Threads are likely stuck waiting on each other's locks\n");

            printf("\n--- Current Balances ---\n");
            for (int i = 0; i < NUM_ACCOUNTS; i++) {
                printf("Account %d: %.2f (%d transactions)\n",
                       i,
                       accounts[i].balance,
                       accounts[i].transaction_count);
            }

            cleanup_mutexes();
            return 0;
        }
    }

    return 0;
}

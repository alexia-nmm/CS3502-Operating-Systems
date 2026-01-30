#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <getopt.h>
#include <signal.h>

volatile sig_atomic_t shutdown_flag = 0;
volatile sig_atomic_t stats_flag = 0;

void handle_sigint(int sig){
shutdown_flag = 1;
}
void handle_sigusr1(int sig){
stats_flag = 1;
}

int main(int argc, char *argv[]){
 int opt;
 int max_lines=-1;
 int verbose = 0;
  
  struct sigaction sa;
  sa.sa_handler = handle_sigint;
  sigemptyset(&sa.sa_mask);
  sa.sa_flags = 0;
  sigaction(SIGUSR1, &sa, NULL);
  while(( opt = getopt(argc, argv, "n:v")) != -1){
    switch(opt){
	case 'n':
		max_lines = atoi(optarg);
		break;
	case 'v':
		verbose = 1;
		break;
	default:
		fprintf(stderr, "Usage: %s [-n max] [-v]\n", argv[0]);
		exit(1);
	}
    }
int c;
int lines = 0;
int chars = 0;
while(!shutdown_flag && ( c = getchar()) != EOF){
  chars++;
  if (c == '\n'){
	lines++;
	if (max_lines != -1 && lines >= max_lines){
	   break;
	}
   }
  if (verbose){
	putchar(c);
   }
  usleep(1000);
  if(stats_flag){
    	fprintf(stderr, "[SIGUSR1] Lines: %d | Characters: %d\n", lines, chars);
	stats_flag = 0;
   }
 }
fprintf(stderr, "Final Lines: %d\n", lines);
fprintf(stderr, "Final Characters: %d\n", chars);
return 0;
}

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <getopt.h>
#include <signal.h>

volatile sig_atomic_t shutdown_flag = 0;

void handle_sigint( int sig){
shutdown_flag = 1;
}
int main(int argc, char *argv[]){
FILE *input = stdin;
char *filename = NULL;
int buffer_size = 4096;
int opt;

struct sigaction sa;
sa.sa_handler = handle_sigint;
sigemptyset(&sa.sa_mask);
sa.sa_flags = 0;
sigaction(SIGINT, &sa, NULL);

while((opt = getopt(argc, argv, "f:b:")) != -1){
 switch(opt){
    case 'f':
	filename = optarg;
	break;
    case 'b' :
	buffer_size = atoi(optarg);
	break;
    default:
	fprintf(stderr, "Usage: %s [-f file] [-b szie] \n", argv[0]);
	exit(1);
	}
}
if (filename != NULL){
 printf("Trying to open file: '%s'\n", filename);
 input = fopen(filename,"r");
 if(input == NULL){
    perror("Error opening file");
    exit(1);
 }
}
char buffer[buffer_size];
size_t bytes_read;

while(!shutdown_flag &&
  (bytes_read = fread(buffer, 1, buffer_size, input))> 0){
  fwrite(buffer,1, bytes_read, stdout);
}
if (filename != NULL){
  fclose(input);
}
if (shutdown_flag){
  fprintf(stderr, "Producer shutting down!\n");
}
return 0;
}

#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <sys/wait.h>

int main(){
 int pipe1[2];
 int pipe2[2];
 pid_t pid;
 char buffer[100];
 
 if (pipe(pipe1) == -1 || pipe(pipe2) == -1){
   perror("pipe failed");
   return 1;
  }
 pid = fork();
 if(pid <0){
  perror("fork failed");
  return 1;
 }
 if(pid == 0){
  close(pipe1[1]);
  close(pipe2[0]);
  read(pipe1[0], buffer, sizeof(buffer));
  printf("Child received: %s\n", buffer);
  char *response = "Hello from child!";
  write(pipe2[1], response, strlen(response) +1);
  close(pipe1[0]);
  close(pipe2[1]);
 }  else {
   close(pipe1[0]);
   close(pipe2[1]);
   char *message = " Hello from parent!";
   write(pipe1[1], message, strlen(message)+1);
   read(pipe2[0], buffer, sizeof(buffer));
   printf("Parent received: %s\n", buffer);
   close(pipe1[1]);
   close(pipe2[0]);
   wait(NULL);
}
return 0;
}

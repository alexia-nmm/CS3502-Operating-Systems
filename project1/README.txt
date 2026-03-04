CS 3502 – Operating Systems
Project 1: Multi-Threaded Banking System
Author: Alexia Martinez

Overview
This project demonstrates different concurrency problems and solutions using a simulated multi-threaded banking system written in C with POSIX threads. The program models bank tellers performing transactions on shared accounts and explores issues such as race conditions, synchronization, deadlock, and deadlock prevention.

Project Structure
The project is divided into four phases:

Phase 1 – Race Condition Demonstration
Multiple threads perform deposits and withdrawals on shared accounts without synchronization. This causes race conditions where the final balances become inconsistent.

Phase 2 – Mutex Protection
Mutex locks are added to protect shared account data. This ensures thread-safe access and produces correct balances across multiple runs.

Phase 3 – Deadlock Creation
A transfer operation requiring two account locks is implemented. Threads lock accounts in opposite order which creates a circular wait and results in a deadlock.

Phase 4 – Deadlock Resolution
Deadlock is prevented using lock ordering. Threads always acquire locks in the same order based on account ID, which eliminates the circular wait condition.

Compilation
Each phase can be compiled using gcc with pthread support.

Example:
gcc -Wall -Wextra -pthread phase1.c -o phase1
gcc -Wall -Wextra -pthread phase2.c -o phase2
gcc -Wall -Wextra -pthread phase3.c -o phase3
gcc -Wall -Wextra -pthread phase4.c -o phase4

Execution
Run each phase separately from the terminal:

./phase1
./phase2
./phase3
./phase4

Dependencies
- GCC compiler
- POSIX Threads (pthread)
- Linux environment (tested using VMware Ubuntu)

Notes
Phase 3 intentionally creates a deadlock for demonstration purposes. Phase 4 resolves this issue using lock ordering to ensure safe concurrent transfers.
Repository
This project is maintained using Git and version control was used throughout development to track changes across each phase of the assignment.

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define PORT 9000
#define BUF 4096

int main() {
    int server_fd, client_fd;
    struct sockaddr_in addr;
    char buffer[1024], filename[128];
    char data[BUF];
    int filesize;
    int received;

    server_fd = socket(AF_INET, SOCK_STREAM, 0);

    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));

    addr.sin_family = AF_INET;
    addr.sin_port = htons(PORT);
    addr.sin_addr.s_addr = INADDR_ANY;

    bind(server_fd, (struct sockaddr*)&addr, sizeof(addr));
    listen(server_fd, 1);

    printf("[SERVER] Waiting for connection on port %d...\n", PORT);
    client_fd = accept(server_fd, NULL, NULL);
    printf("[SERVER] Client connected!\n");

    // --- receive filename ---
    recv(client_fd, buffer, sizeof(buffer), 0);
    sscanf(buffer, "SEND %s", filename);
    printf("[SERVER] Receiving file: %s\n", filename);
    send(client_fd, "OK\n", 3, 0);

    // --- receive size ---
    recv(client_fd, buffer, sizeof(buffer), 0);
    sscanf(buffer, "SIZE %d", &filesize);
    printf("[SERVER] File size: %d bytes\n", filesize);
    send(client_fd, "OK\n", 3, 0);

    // --- receive binary data ---
    FILE *f = fopen(filename, "wb");
    received = 0;
    while (received < filesize) {
        int n = recv(client_fd, data, BUF, 0);
        fwrite(data, 1, n, f);
        received += n;
    }
    fclose(f);

    printf("[SERVER] File saved.\n");
    send(client_fd, "DONE\n", 5, 0);

    close(client_fd);
    close(server_fd);

    return 0;
}

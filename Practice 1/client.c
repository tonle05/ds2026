#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <arpa/inet.h>

#define BUF 4096

int main(int argc, char *argv[]) {
    if (argc != 4) {
        printf("Usage: %s <server_ip> <port> <file>\n", argv[0]);
        return 0;
    }

    char *server_ip = argv[1];
    int port = atoi(argv[2]);
    char *filename = argv[3];

    int sock = socket(AF_INET, SOCK_STREAM, 0);
    struct sockaddr_in addr;

    addr.sin_family = AF_INET;
    addr.sin_port = htons(port);
    inet_pton(AF_INET, server_ip, &addr.sin_addr);

    connect(sock, (struct sockaddr*)&addr, sizeof(addr));
    printf("[CLIENT] Connected to server.\n");

    // get file size
    FILE *f = fopen(filename, "rb");
    fseek(f, 0, SEEK_END);
    int filesize = ftell(f);
    fseek(f, 0, SEEK_SET);

    char buffer[1024];
    char data[BUF];

    // SEND filename
    sprintf(buffer, "SEND %s\n", filename);
    send(sock, buffer, strlen(buffer), 0);
    recv(sock, buffer, sizeof(buffer), 0);

    // SEND size
    sprintf(buffer, "SIZE %d\n", filesize);
    send(sock, buffer, strlen(buffer), 0);
    recv(sock, buffer, sizeof(buffer), 0);

    // SEND file data
    int n;
    while ((n = fread(data, 1, BUF, f)) > 0) {
        send(sock, data, n, 0);
    }
    fclose(f);

    recv(sock, buffer, sizeof(buffer), 0);
    printf("[CLIENT] Transfer complete.\n");

    close(sock);
    return 0;
}

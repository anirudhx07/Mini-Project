/**
 * @file esp32_cam_vga.ino
 * @brief Separate AI Thinker ESP32-CAM OV2640 VGA (640x480) MJPEG Stream Firmware for COCKPIT
 *
 * Hardware:
 *   - Board: AI Thinker ESP32-CAM
 *   - Sensor: OV2640
 *   - Programmer: ESP32-CAM-MB
 *
 * Endpoints:
 *   - http://<ESP32-CAM-IP>/          (Lightweight HTTP health check for COCKPIT)
 *   - http://<ESP32-CAM-IP>:81/stream (Low-latency VGA MJPEG stream)
 *
 * Before flashing:
 *   1. Copy secrets.h.example -> secrets.h and set your Wi-Fi SSID/password.
 *   2. In Arduino IDE: Board = "AI Thinker ESP32-CAM", PSRAM = "Enabled".
 */

#include "esp_camera.h"
#include "esp_http_server.h"
#include <WiFi.h>

#if __has_include("secrets.h")
    #include "secrets.h"
#else
    #error "Missing secrets.h! Copy secrets.h.example to secrets.h and set WIFI_SSID / WIFI_PASSWORD."
#endif

// AI Thinker ESP32-CAM Pin Mapping
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

#define STREAM_BOUNDARY "123456789000000000000987654321"
static const char* STREAM_CONTENT_TYPE = "multipart/x-mixed-replace;boundary=" STREAM_BOUNDARY;
static const char* STREAM_BOUNDARY_STR = "\r\n--" STREAM_BOUNDARY "\r\n";
static const char* STREAM_PART_HDR     = "Content-Type: image/jpeg\r\nContent-Length: %u\r\n\r\n";

httpd_handle_t status_httpd = NULL;
httpd_handle_t stream_httpd = NULL;

static esp_err_t health_handler(httpd_req_t *req) {
    httpd_resp_set_type(req, "application/json");
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");
    const char* body = "{\"status\":\"ok\",\"camera\":\"ESP32-CAM OV2640\",\"resolution\":\"640x480\"}";
    return httpd_resp_send(req, body, strlen(body));
}

static esp_err_t stream_handler(httpd_req_t *req) {
    camera_fb_t *fb = NULL;
    esp_err_t res = ESP_OK;
    char part_buf[64];

    res = httpd_resp_set_type(req, STREAM_CONTENT_TYPE);
    if (res != ESP_OK) return res;
    httpd_resp_set_hdr(req, "Access-Control-Allow-Origin", "*");

    while (true) {
        fb = esp_camera_fb_get();
        if (!fb) {
            res = ESP_FAIL;
            break;
        }

        size_t hlen = snprintf(part_buf, sizeof(part_buf), STREAM_PART_HDR, fb->len);
        res = httpd_resp_send_chunk(req, STREAM_BOUNDARY_STR, strlen(STREAM_BOUNDARY_STR));
        if (res == ESP_OK) {
            res = httpd_resp_send_chunk(req, part_buf, hlen);
        }
        if (res == ESP_OK) {
            res = httpd_resp_send_chunk(req, (const char *)fb->buf, fb->len);
        }

        esp_camera_fb_return(fb);
        fb = NULL;

        if (res != ESP_OK) {
            break;
        }
    }
    return res;
}

void startCameraServers() {
    httpd_config_t config = HTTPD_DEFAULT_CONFIG();
    config.server_port = 80;

    httpd_uri_t health_uri = {
        .uri      = "/",
        .method   = HTTP_GET,
        .handler  = health_handler,
        .user_ctx = NULL
    };
    if (httpd_start(&status_httpd, &config) == ESP_OK) {
        httpd_register_uri_handler(status_httpd, &health_uri);
    }

    httpd_config_t stream_cfg = HTTPD_DEFAULT_CONFIG();
    stream_cfg.server_port = 81;
    stream_cfg.ctrl_port   = 32769;

    httpd_uri_t stream_uri = {
        .uri      = "/stream",
        .method   = HTTP_GET,
        .handler  = stream_handler,
        .user_ctx = NULL
    };
    if (httpd_start(&stream_httpd, &stream_cfg) == ESP_OK) {
        httpd_register_uri_handler(stream_httpd, &stream_uri);
    }
}

void setup() {
    Serial.begin(115200);
    Serial.setDebugOutput(false);
    Serial.println();

    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer   = LEDC_TIMER_0;
    config.pin_d0       = Y2_GPIO_NUM;
    config.pin_d1       = Y3_GPIO_NUM;
    config.pin_d2       = Y4_GPIO_NUM;
    config.pin_d3       = Y5_GPIO_NUM;
    config.pin_d4       = Y6_GPIO_NUM;
    config.pin_d5       = Y7_GPIO_NUM;
    config.pin_d6       = Y8_GPIO_NUM;
    config.pin_d7       = Y9_GPIO_NUM;
    config.pin_xclk     = XCLK_GPIO_NUM;
    config.pin_pclk     = PCLK_GPIO_NUM;
    config.pin_vsync    = VSYNC_GPIO_NUM;
    config.pin_href     = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn     = PWDN_GPIO_NUM;
    config.pin_reset    = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;       // 20 MHz XCLK
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size   = FRAMESIZE_VGA;  // 640x480 default (SVGA 800x600 supported when PSRAM present)
    config.jpeg_quality = 12;

    if (psramFound()) {
        config.fb_count  = 2;
        config.grab_mode = CAMERA_GRAB_LATEST;
    } else {
        config.fb_count  = 1;
        config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
    }

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed with error 0x%x\n", err);
        return;
    }

    // Do NOT override frame_size to QVGA after initialization.
    sensor_t *s = esp_camera_sensor_get();
    if (s != NULL) {
        s->set_framesize(s, FRAMESIZE_VGA);
    }

    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    WiFi.setSleep(false);
    Serial.print("Connecting to Wi-Fi");
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
    }
    Serial.println();

    startCameraServers();

    Serial.print("Camera Ready! Stream URL: http://");
    Serial.print(WiFi.localIP());
    Serial.println(":81/stream");
}

void loop() {
    delay(10000);
}

#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import json
import gzip
import string
import datetime


# log_format ui_short '$remote_addr $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';


LOG_LINE_REGEXP = re.compile(r"\"(.*?)\"|\[(.*?)\]|(\S+)")
LOG_NAME_REGEXP = re.compile(r"nginx-access-ui\.log-(\d\d\d\d)(\d\d)(\d\d)\.gz")

def get_line(line):
    """парсит конкретную запись лога и возвращает словарик с нужными данными"""
    parsed_line = {}
    line_elements = map(''.join, LOG_LINE_REGEXP.findall(line))
    request = line_elements[4]
    try:
        method, url, http = request.split()
    except:
        return parsed_line
    dt = line_elements[3].split()[0]
    parsed_line = {
        "ip": line_elements[0],
        "datetime": datetime.datetime.strptime(dt, '%d/%b/%Y:%H:%M:%S'),
        "status": int(line_elements[5]),
        "method": method,
        "url": url,
        "time": float(line_elements[-1])
    }
    return parsed_line

def readln(file_path):
    """генератор для прохода по файлу лога"""
    if file_path.endswith(".gz"):
        log = gzip.open(file_path, 'rb')
    else:
        log = open(file_path)
    total_lns = 0
    processed_lns = 0
    for line in log:
        parsed_line = get_line(line)
        total_lns += 1
        if parsed_line:
            processed_lns += 1
            yield parsed_line
    log.close()


def save_report(path, dst_path, rep_size, report, format ):
    """сохраняем отчет"""

    if format == "json":
        with open(path) as rp:
            rp.write(json.dumps(report))
    elif format=="html":
        tbl_json = json.dumps(report)
        with open("report.html") as f:
            tpl = string.Template(f.read())
            html = tpl.safe_substitute(table_json=tbl_json)
            sv_path = dst_path + ".html"
            print "Сохраняем %s " % sv_path
            with open(sv_path, "w") as rp_html:
                rp_html.write(html)




def prepare_report(path, report_size):
    """подготавливает данные для отчета"""
    log_figures = {}
    empty_row = lambda:{
        "count":0, "count_perc": 0.0, "time_perc": 0.0,
        "time_sum":0.0, "time_avg":0.0, "times":[], "time_max":0.0,
        "time_med": 0.0,
    }
    total_time = 0.0
    total_cnt = 0.0

    log_generator = readln(path)
    cnt = 0
    for row in log_generator:
        url, tm = row["url"], row["time"]
        rec = log_figures.get(url, None)
        if rec is None:
            rec = empty_row()
            log_figures[url] = rec
        rec["count"] += 1
        rec["time_sum"] += tm
        rec["times"].append(tm)
        total_cnt += 1
        total_time += tm
        cnt += 1

    for url, rec in log_figures.items():
        rec["url"] = url
        rec["count_perc"] = round(rec["count"] * 100 / total_cnt, 3)
        rec["time_perc"] = round(rec["time_sum"] * 100 / total_time, 3)
        rec["time_avg"] = round(rec["time_sum"] * 100 / total_cnt, 3)
        rec["time_med"] = sorted(rec["times"])[(len(rec["times"])-1)/2]
        rec["time_sum"] = round(rec["time_sum"],3)
        rec["time_max"] = max(rec["times"])
        del rec["times"]

    report = log_figures.values()
    return sorted(report, key=lambda d: d["time_sum"], reverse=True)[:report_size]


def check_report(log_dir):
    logs = []
    today = datetime.date.today()
    for f in os.listdir(log_dir):
        match = LOG_NAME_REGEXP.match(f)
        if match:
            log_dt = datetime.date(*map(int, match.groups()))
            if log_dt != today:
                log_name = f
                logs.append((log_name, log_dt))
    if logs:
        nm, dt = max(logs, key=lambda p: p[1])
        pth = os.path.join(log_dir, nm)
    else:
        nm = dt = pth = None
    return (nm,dt,pth)


def is_processed(rep_dir,dt):
    for f in os.listdir(rep_dir):
        date_str = f.split("-")[1].rsplit(".", 1)[0]
        rep_dt = datetime.datetime.strptime(date_str, "%Y.%m.%d").date()
        if dt == rep_dt:
            return True
    return False


def main():
    rep_dir = "./reports"
    log_dir = "./log"
    rep_size = 1000
    if not os.path.exists(rep_dir):
        os.makedirs(rep_dir)
    name, date, path = check_report(log_dir)

    if path and not is_processed(rep_dir, date):
        print "Обработка файла %s..." % path
        lg_dt = "Повтор %s" % date if path and is_processed(rep_dir, date) else date
        sv_path = os.path.join(rep_dir, "report-%s" % lg_dt)
        report = prepare_report(path, rep_size)
        save_report(path, sv_path, rep_size, report, format="html")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Produce a concise French report without equating CPU time and energy."""
import argparse
from datetime import datetime
from analyze import analyze, records


def local_time(value):
    if not isinstance(value, str):
        return 'indisponible'
    try:
        return datetime.fromisoformat(value.replace('Z', '+00:00')).astimezone().strftime('%d/%m %H:%M:%S %Z')
    except ValueError:
        return value


def render(rows):
    report = analyze(rows)
    samples = [r for r in rows if r.get('event') == 'sample']
    output = ['# Diagnostic batterie', '', f"Échantillons : {len(samples)}."]
    if samples:
        output.append(f"Période échantillonnée : {local_time(samples[0].get('wall_utc'))} à {local_time(samples[-1].get('wall_utc'))}.")
    findings = {item['kind']: item for item in report['findings']}
    if 'suspend_counter_delta' in findings:
        data = findings['suspend_counter_delta']
        output.append(f"Suspensions réussies : {data['success'] if data['success'] is not None else 'indéterminé'} ; échecs : {data['fail'] if data['fail'] is not None else 'indéterminé'}.")
    if 'sleep_inhibitors_seen_without_success_delta' in findings:
        output.extend(['', '## Inhibiteurs de veille observés', ''])
        for holder in findings['sleep_inhibitors_seen_without_success_delta']['holders']:
            output.append(f"- {holder.get('who') or 'inconnu'} : présent à {holder['samples_seen']} échantillon(s), motif : {holder.get('why') or 'non précisé'}.")
        output.append('Ces présences ne prouvent pas à elles seules la cause de l’absence de veille.')
    cpu = findings.get('observed_cpu_activity')
    if cpu:
        hz = next((r.get('clock_ticks_per_second') for r in samples if isinstance(r.get('clock_ticks_per_second'), int) and r['clock_ticks_per_second'] > 0), None)
        output.extend(['', '## Activité CPU observée', '', 'Classement limité aux processus mesurés ; ce ne sont pas des watts ni une attribution de consommation électrique.'])
        for p in cpu['processes'][:5]:
            value = f"{p['cpu_tick_delta'] / hz:.2f} s CPU" if hz else f"{p['cpu_tick_delta']} ticks CPU"
            output.append(f"- {p.get('comm') or 'inconnu'} (PID {p['pid']}) : {value} ; {', '.join(p.get('cgroup_units') or ['service non identifié'])}.")
    if samples:
        first = samples[0].get('battery', {}).get('qcom-battery', {})
        last = samples[-1].get('battery', {}).get('qcom-battery', {})
        statuses = {'Charging': 'en charge', 'Discharging': 'en décharge', 'Full': 'pleine', 'Not charging': 'ne charge pas'}
        first_status = statuses.get(first.get('status'), first.get('status', 'état inconnu'))
        last_status = statuses.get(last.get('status'), last.get('status', 'état inconnu'))
        output.extend(['', '## Batterie', '', f"Premier relevé : {first.get('capacity', '?')} % ({first_status}) ; dernier : {last.get('capacity', '?')} % ({last_status})."])
        if last.get('status') == 'Charging':
            output.append('Le dernier relevé est déjà en charge : il ne représente pas une fin de décharge isolée.')
    output.extend(['', '## Limites', '', 'Les observations ne prouvent pas à elles seules la cause de la décharge. Le relevé ne mesure pas les watts par application.'])
    for warning in report.get('warnings', []):
        if 'legacy process entries lack start_ticks' in warning:
            output.append('- Ancienne capture : classement CPU non calculé, car les identités de processus ne permettent pas d’exclure une réutilisation de PID.')
        elif 'outside the per-sample top-process cap' in warning:
            output.append('- Certains processus actifs sont exclus par la limite du nombre de processus relevés.')
        else:
            output.append(f'- {warning}')
    return '\n'.join(output) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('capture')
    args = parser.parse_args()
    print(render(list(records(args.capture))), end='')


if __name__ == '__main__':
    main()

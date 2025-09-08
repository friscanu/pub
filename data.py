import os
import json
import pandas as pd
import xml.etree.ElementTree as ET

def get_proxy_base_path(proxies_xml_path):
    if not os.path.exists(proxies_xml_path):
        return None
    try:
        tree = ET.parse(proxies_xml_path)
        root = tree.getroot()
        base_path_elem = root.find('.//BasePath')
        if base_path_elem is not None and base_path_elem.text:
            return base_path_elem.text.strip()
    except ET.ParseError:
        return None
    return None

def parse_policy(policy_path):
    try:
        tree = ET.parse(policy_path)
        root = tree.getroot()
        return root.tag
    except ET.ParseError:
        return "Unknown"

def parse_target(target_path):
    target_name = os.path.basename(target_path)[:-4] if target_path.endswith('.xml') else os.path.basename(target_path)
    target_info = 'Unknown'
    if not os.path.exists(target_path):
        return target_name, target_info
    try:
        tree = ET.parse(target_path)
        root = tree.getroot()
        http_target = root.find('.//HTTPTargetConnection')
        if http_target is not None:
            url_elem = http_target.find('URL')
            if url_elem is not None and url_elem.text:
                target_info = url_elem.text.strip()
            else:
                host = http_target.find('Host')
                port = http_target.find('Port')
                path = http_target.find('Path')
                host_text = host.text.strip() if host is not None and host.text else ''
                port_text = f":{port.text.strip()}" if port is not None and port.text else ''
                path_text = path.text.strip() if path is not None and path.text else ''
                if host_text:
                    target_info = f"http://{host_text}{port_text}{path_text}"
    except ET.ParseError:
        target_info = 'Unknown'
    return target_name, target_info

def parse_proxy(proxy_path, folder_name):
    proxy_name = folder_name
    if proxy_name.endswith('.xml'):
        proxy_name = proxy_name[:-4]

    policies_dir = os.path.join(proxy_path, 'policies')
    policy_names = []
    policy_types = []
    if os.path.exists(policies_dir):
        for policy_file in os.listdir(policies_dir):
            if policy_file.endswith('.xml'):
                policy_names.append(policy_file[:-4])
                policy_types.append(parse_policy(os.path.join(policies_dir, policy_file)))
    policies_str = ", ".join(policy_names) if policy_names else "No Policies"
    policy_types_str = ", ".join(policy_types) if policy_types else "Unknown"

    proxies_xml_path = os.path.join(proxy_path, 'proxies', 'default.xml')
    base_path = get_proxy_base_path(proxies_xml_path) or 'Unknown'

    targets_dir = os.path.join(proxy_path, 'targets')
    target_names = []
    target_infos = []
    if os.path.exists(targets_dir):
        for target_file in os.listdir(targets_dir):
            if target_file.endswith('.xml'):
                t_name, t_info = parse_target(os.path.join(targets_dir, target_file))
                target_names.append(t_name)
                target_infos.append(t_info)
    target_names_str = ", ".join(target_names) if target_names else "No Targets"
    target_infos_str = ", ".join(target_infos) if target_infos else "Unknown"

    return {
        'Proxy Name': proxy_name,
        'Policies': policies_str,
        'Policy Types': policy_types_str,
        'Policy Count': len(policy_names),
        'Proxy Path': base_path,
        'Target Server Name': target_names_str,
        'Target Server Info': target_infos_str
    }

def parse_sharedflow(sharedflow_path):
    sharedflow_name = os.path.basename(sharedflow_path)
    policies_dir = os.path.join(sharedflow_path, 'policies')
    policies = []
    if os.path.exists(policies_dir):
        policies = [p[:-4] for p in os.listdir(policies_dir) if p.endswith('.xml')]
    return {
        'Shared Flow Name': sharedflow_name,
        'Number of Policies': len(policies),
        'Policies': ", ".join(policies) if policies else "No Policies"
    }

def count_json_files(path):
    if not os.path.exists(path):
        return 0
    count = 0
    for root, dirs, files in os.walk(path):
        count += len([f for f in files if f.endswith('.json')])
    return count

def extract_temp_summary(temp_path):
    artifact_counts = {}
    if not os.path.exists(temp_path):
        return artifact_counts
    keys_to_count = [
        'apiproducts',
        'apps',
        'developerApps',
        'developers',
        'importKeys',
        'keyvaluemaps',
        'eval/aliases',
        'eval/flowhooks',
        'eval/keystores',
        'eval/keyvaluemaps',
        'eval/targetservers',
    ]
    for key in keys_to_count:
        folder_path = os.path.join(temp_path, key)
        artifact_counts[key] = count_json_files(folder_path)
    return artifact_counts

def extract_artifacts_detailed(temp_path):
    """ Extracts artifact info by type and name from temp folder """
    artifacts = []
    if not os.path.exists(temp_path):
        return artifacts
    keys_to_extract = [
        'apiproducts',
        'apps',
        'developerApps',
        'developers',
        'importKeys',
        'keyvaluemaps',
        'eval/aliases',
        'eval/flowhooks',
        'eval/keystores',
        'eval/keyvaluemaps',
        'eval/targetservers',
    ]
    for key in keys_to_extract:
        folder_path = os.path.join(temp_path, key)
        if not os.path.exists(folder_path):
            continue
        # Special case: developerApps may have subfolders with JSON inside
        if key == 'developerApps':
            for dev_folder in os.listdir(folder_path):
                dev_path = os.path.join(folder_path, dev_folder)
                if os.path.isdir(dev_path):
                    for f in os.listdir(dev_path):
                        if f.endswith('.json'):
                            artifact_name = f[:-5]
                            artifacts.append({'Artifact Type': key, 'Artifact Name': artifact_name, 'Artifact Count': 1})
        else:
            for f in os.listdir(folder_path):
                if f.endswith('.json'):
                    artifact_name = f[:-5]
                    artifacts.append({'Artifact Type': key, 'Artifact Name': artifact_name, 'Artifact Count': 1})
    return artifacts

def main(base_dir):
    # Proxies
    proxies_dir = os.path.join(base_dir, 'proxies')
    proxies_data = []
    for proxy_folder in sorted(os.listdir(proxies_dir)):
        proxy_apiproxy_path = os.path.join(proxies_dir, proxy_folder, 'apiproxy')
        if os.path.isdir(proxy_apiproxy_path):
            proxy_data = parse_proxy(proxy_apiproxy_path, proxy_folder)
            proxies_data.append(proxy_data)
    df_proxies = pd.DataFrame(proxies_data)

    # Shared Flows - as artifacts
    shared_flows_dir = os.path.join(base_dir, 'sharedflows')
    sharedflows_artifacts = []
    if os.path.exists(shared_flows_dir):
        for sf_folder in os.listdir(shared_flows_dir):
            sf_path = os.path.join(shared_flows_dir, sf_folder, 'sharedflowbundle')
            if os.path.isdir(sf_path):
                sharedflows_artifacts.append({'Artifact Type': 'sharedflow', 'Artifact Name': sf_folder, 'Artifact Count': 1})

    # Extract detailed artifacts from temp
    temp_dir = os.path.join(base_dir, 'temp')
    detailed_artifacts = extract_artifacts_detailed(temp_dir)

    # Combine sharedflows and temp detailed artifacts
    all_artifacts = sharedflows_artifacts + detailed_artifacts
    df_other_org = pd.DataFrame(all_artifacts)

    # Filter out flowhooks and apps
    df_other_org = df_other_org[~df_other_org['Artifact Type'].isin(['eval/flowhooks', 'apps'])]

    # For importKeys, set Artifact Name to "N/A"
    df_other_org.loc[df_other_org['Artifact Type'] == 'importKeys', 'Artifact Name'] = 'N/A'

    # --- Continue with summary calculations ---
    
    total_proxies = len(df_proxies)
    total_policies = df_proxies['Policy Count'].sum() if not df_proxies.empty else 0
    total_sharedflows = len(sharedflows_artifacts)

    artifact_type_counts = df_other_org.groupby('Artifact Type').size().to_dict()

    summary_rows = [
        {'Metric': 'Total Proxies', 'Count': total_proxies},
        {'Metric': 'Total Policies', 'Count': total_policies},
        {'Metric': 'Total Shared Flows', 'Count': total_sharedflows}
    ]
    for artifact_type, count in artifact_type_counts.items():
        summary_rows.append({'Metric': artifact_type, 'Count': count})

    df_summary = pd.DataFrame(summary_rows)

    # Write Excel with updated df_other_org and df_summary as before
    # Writ Excel
    excel_path = os.path.join(base_dir, 'apigee_full_report_with_artifacts_detailed.xlsx')
    if os.path.exists(excel_path):
        os.remove(excel_path)

    with pd.ExcelWriter(excel_path, engine='xlsxwriter') as writer:
        df_proxies.to_excel(writer, sheet_name='Proxy Details', index=False)
        if not df_other_org.empty:
            df_other_org.to_excel(writer, sheet_name='Other Org Details', index=False)
        df_summary.to_excel(writer, sheet_name='Summary', index=False)
        print(f"Sheets written: {list(writer.sheets.keys())}")

    print(f"Report with detailed artifacts completed: {excel_path}")

if __name__ == "__main__":
    base_export_folder = "./apigee-x-testing-469312"  # Update path as needed
    main(base_export_folder)

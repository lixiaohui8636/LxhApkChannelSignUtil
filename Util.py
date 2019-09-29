import os
import shutil
from xml.etree import ElementTree as ET


def signApk(temp_unsign_apk_dir, unsign_apk_file_name, out_sign_file_dir, keystore_path, keystore_pwd, keystore_alias_name):
    # unsignedjar = r'./bin/%s_%s_unsigned.apk' % (easyName, value)
    # signed_unalignedjar = r'./bin/%s_%s_signed_unaligned.apk' % (easyName, value)
    # signed_alignedjar = r'./bin/%s_%s.apk' % (easyName, value)
    # cmd_sign = r'jarsigner -verbose -keystore %s -storepass %s -signedjar %s %s %s' % (
    # keystore, storepass, signed_unalignedjar, unsignedjar, alianame)
    # cmd_align = r'zipalign -v 4 %s %s' % (signed_unalignedjar, signed_alignedjar)
    # os.system(cmd_sign)
    # os.remove(unsignedjar)
    # os.system(cmd_align)
    # os.remove(signed_unalignedjar)
    unsign_file_name_list = os.path.splitext(unsign_apk_file_name)
    v1_sign_apk_path = temp_unsign_apk_dir+"/"+unsign_file_name_list[0]+"_v1sign"+unsign_file_name_list[1]
    unsign_apk_path = temp_unsign_apk_dir+"/"+unsign_apk_file_name
    # V1签名
    sign_v1_cmd = r'jarsigner -verbose -keystore %s -storepass %s -signedjar %s %s %s' % (
        keystore_path, keystore_pwd, v1_sign_apk_path, unsign_apk_path, keystore_alias_name)
    os.system(sign_v1_cmd)
    check_v1_sign_cmd = r'jarsigner -verify -verbose %s' % (v1_sign_apk_path)
    os.system(check_v1_sign_cmd)
    # zipalign
    if not os.path.exists(out_sign_file_dir):
        os.makedirs(out_sign_file_dir)

    v1_sign_zip_apk_path = out_sign_file_dir+"/"+unsign_file_name_list[0]+"_sign_zip"+unsign_file_name_list[1]
    zip_align_cmd = r'zipalign -v 4 %s %s' % (v1_sign_apk_path,v1_sign_zip_apk_path)
    os.system(zip_align_cmd)
    # v2签名
    sign_v2_cmd = 'apksigner sign --ks %s --ks-pass pass:%s --ks-key-alias %s %s' % (
        keystore_path, keystore_pwd, keystore_alias_name, v1_sign_zip_apk_path)
    os.system(sign_v2_cmd)


# 备份manifest文件
def backUpManifest(back_manifest_dir, temp_manifest_path):
    back_up_manifest_file_path = back_manifest_dir + "/AndroidManifest.xml"
    print("back_manifest:" + back_up_manifest_file_path)
    print("temp_manifest:" + temp_manifest_path)
    # 如果存在删除以前的文件
    if os.path.exists(back_manifest_dir):
        print("删除：" + back_manifest_dir)
        shutil.rmtree(back_manifest_dir)
    os.makedirs(back_manifest_dir)
    # 复制temp到back的路径
    shutil.copy(temp_manifest_path, back_up_manifest_file_path)
    return back_up_manifest_file_path


def modifyChannel(channel, back_up_manifest_file_path, temp_manifest_path, unzip_temp_dir, temp_dir, apk_file,
                  out_sign_file_dir, keystore_path, keystore_pwd, keystore_alias_name):
    android_ns = 'http://schemas.android.com/apk/res/android'
    print(channel)
    # 替换channel value
    ET.register_namespace('android', android_ns)
    tree = ET.parse(back_up_manifest_file_path)
    root = tree.getroot()
    key = '{' + android_ns + '}name'
    val = '{' + android_ns + '}value'
    app_node = root.find('application')
    if app_node is None:
        return
    meta_data_list = app_node.findall('meta-data')
    if meta_data_list is not None:
        for metaDataNode in meta_data_list:
            key_name = metaDataNode.attrib[key]
            # if keyName == 'UMENG_CHANNEL' or keyName == 'DC_CHANNEL' or keyName == 'channel_value':
            if key_name == 'UMENG_CHANNEL':
                metaDataNode.set(val, channel)
    tree.write(temp_manifest_path, 'UTF-8')
    file_name_list = os.path.splitext(os.path.basename(apk_file))
    #temp/test_legu_lxh/
    temp_unsign_apk_dir = temp_dir + "/" + file_name_list[0]

    unsign_apk_file_name = file_name_list[0] + "_"+channel+"_unsigned" + file_name_list[1]
    # 生成未签名的apk
    unsign_apk_file_path = temp_unsign_apk_dir + "/" + unsign_apk_file_name
    print("生成未签名apk:" + unsign_apk_file_path)
    apk_tool_unsign_apk_cmd = r'java -jar apktool_2.4.0.jar -p %s b %s -o %s' % (
        "./framework", unzip_temp_dir, unsign_apk_file_path)
    os.system(apk_tool_unsign_apk_cmd)
    # 签名
    signApk(temp_unsign_apk_dir, unsign_apk_file_name, out_sign_file_dir, keystore_path, keystore_pwd, keystore_alias_name)


def channelApk(apk_file, channel_list, out_sign_file_dir, keystore_path, keystore_pwd, keystore_alias_name):
    print("开始多渠道打包，原Apk路径为：" + apk_file)
    apk_dir = os.path.dirname(apk_file)
    temp_dir = apk_dir + "/temp"
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir)
    # 解压的文件路径
    unzip_temp_dir = temp_dir + "/channelTemp"
    print(unzip_temp_dir)
    # 判断是否有文件，否则删除
    if os.path.exists(unzip_temp_dir):
        print("删除：" + unzip_temp_dir)
        shutil.rmtree(unzip_temp_dir)
    # 创建临时目录
    os.makedirs(unzip_temp_dir)

    # apktool解压apk
    apk_tool_unzip_cmd = r'java -jar apktool_2.4.0.jar -p %s d -f -s %s  -o %s' % (
        "./framework", apk_file, unzip_temp_dir)
    os.system(apk_tool_unzip_cmd)
    # 得到解压的manifest文件路径
    temp_manifest_path = unzip_temp_dir + "/AndroidManifest.xml"
    # 备份一份到
    back_manifest_dir = temp_dir + "/manifestBackUp"
    back_up_manifest_file_path = backUpManifest(back_manifest_dir, temp_manifest_path)
    # 去执行每一个
    for channel in channel_list:
        modifyChannel(channel, back_up_manifest_file_path, temp_manifest_path, unzip_temp_dir, temp_dir, apk_file,
                  out_sign_file_dir, keystore_path, keystore_pwd, keystore_alias_name)

    print("success")



#-----------------------------------------------------------------
# Vitis v2024.2 (64-bit)
# Start of session at: Fri Feb 21 10:36:28 2025
# Current directory: E:\repos\FreeRTOS_Test
# Command line: vitis -i
# Journal file: vitis_journal.py
# Batch mode: $XILINX_VITIS/bin/vitis -new -s E:\repos\FreeRTOS_Test\vitis_journal.py
#-----------------------------------------------------------------

#!/usr/bin/env python3
import vitis, os, shutil, time

def rename_with_retry(name1, name2, max_retries):
    #hack because rename is a bit unreliable
    retry_count = 0
    while 1:
        try:
            os.rename(name1, name2)
            break
        except OSError:
            if retry_count > max_retries:
                raise
            else:
                retry_count += 1
                time.sleep(0)

client = vitis.create_client()
client.update_workspace(".")
#[Out]# True
client.set_workspace(".")
#[Out]# True
platform_obj=client.create_platform_component(name="platform", hw_design="System_wrapper.xsa", cpu="ps7_cortexa9_0", os = "standalone")
domain0_obj = platform_obj.get_domain("standalone_ps7_cortexa9_0")
domain0_obj.set_lib(lib_name = 'xilrsa')
#[Out]# True
domain0_obj.set_config(option = 'lib', lib_name = 'xiltimer', param = 'XILTIMER_en_interval_timer', value = 'true')
#[Out]# True
domain0_obj.set_config(option = 'lib', lib_name = 'xiltimer', param = 'XILTIMER_tick_timer', value = 'ps7_scutimer_0')
#[Out]# True

#apply bsp patch
shutil.copytree("rtos_test/src/external/FreeRTOS_Zynq_Port/bsp_patch", "platform/ps7_cortexa9_0/standalone_ps7_cortexa9_0/bsp/libsrc/standalone/src/arm/cortexa9/gcc", dirs_exist_ok=True)

platform_obj.build()
#[Out]# 0
platform_ps7 = client.find_platform_in_repos("platform")

rename_with_retry("rtos_test", "rtos_test_", 10)

app0_obj = client.create_app_component(name = "rtos_test", platform = platform_ps7, domain = "standalone_ps7_cortexa9_0")

shutil.copytree("rtos_test_/src", "rtos_test/src", dirs_exist_ok=True)
shutil.rmtree("rtos_test_")

app0_obj.build()
#[Out]# 0
exit()
vitis.dispose()

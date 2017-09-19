#!/bin/bash

mkdir -p /.trash
mkdir -p ~/.trash

cat >> /etc/profile << EOF
undelfile()
{
    for file in \$@
    do
        if [ ! -f "$HOME/.trash/\${file#/}" ] && [ ! -d "$HOME/.trash/\${file#/}" ]
        then
            similar=\$(find ~/.trash/ -name \$(basename \${file}) | grep "\${file}")
            if [ -z "\$(sed 's/\s//g' <<< \${similar})" ]
            then
                echo "回收站内未找到指定文件进行还原"
            else
                echo "未找到指定文件，类似文件如下，请确认："
                similar_array=(\${similar})
                for sfile in \${similar_array[@]}
                do
                    echo \${sfile#~/.trash}
                done
            fi
            return 1
        elif [ -f "$HOME/.trash/\${file#/}" ]
        then
            if [ -f "\${file}" ]
            then
                read -p "文件 \${file} 已存在，是否覆盖[n]?" confirm
                if [ "\${confirm}" == "y" ] || [ "\${confirm}" == "Y" ]
                then
                    /bin/mv ~/.trash/\${file#/} \${file}
                else
                    return 1
                fi
            else
                /bin/mv ~/.trash/\${file#/} \${file}
            fi
        elif [ -d "\$HOME/.trash/\${file#/}" ]
        then
            if [ ! -d "\${file}" ]
            then
                mkdir -p \${file}
            else
                files=\$(find ~/.trash/\${file#/} | sed "s@^\$HOME/.trash@@g")
                file_array=(\${files})
                for sfile in \${file_array[@]}
                do
                    if [ ! -d "\$(dirname \${sfile})" ]
                    then
                        mkdir -p \$(dirname \${sfile})
                    fi
                    /bin/mv ~/.trash/\${sfile#/} \$(dirname \${sfile}) &> /dev/null
                done
            fi
        fi
    done
    return 0
}
trash()
{
    for file in \$@
    do
        cd \$(dirname \$file) &> /dev/null
        dirpath=\$(pwd)
        mkdir -p ~/.trash/\${dirpath#/}
        /bin/mv \$(basename \${file}) ~/.trash/\${dirpath#/}
        cd - &> /dev/null
    done
}
cleartrash()
{
    read -p "clear sure?[n]" confirm
    [ "\${confirm}" == "y" ] || [ "\${confirm}" == "Y" ] && /bin/rm -rf ~/.trash/*
}
alias rm=trash
alias r=trash
alias lr='find /root/.trash/ -type f |sed "s@^$HOME/.trash@@g"'
alias ur=undelfile
EOF
import os

def generate_test(ques_path, simility_question_path, save_path):
    ques_dict = {}
    with open(simility_question_path, r'r', encoding='utf-8') as fr:
        for line in fr:
            ques, simility = line.strip('\n').split('----')[0].replace('?', '').replace('？', ''), line.strip('\n').split('----')[1]
            if ques not in ques_dict.keys():
                ques_dict[ques] = [simility]
            else:
                ques_dict[ques].append(simility)

    max_list = 0
    for item in ques_dict.keys():
        if len(ques_dict[item]) > max_list:
            max_list = len(ques_dict[item])

    for idx in range(max_list):
        with open(os.path.join(save_path, '{}.txt'.format(idx)), r'w', encoding='utf-8') as fw:
            with open(ques_path, r'r', encoding='utf-8') as fr:
                for line in fr:
                    ques = line.strip('\n').replace('?', '').replace('？', '')
                    if ques in ques_dict.keys():
                        answer = ques_dict[ques][idx] if len(ques_dict[ques]) > idx else ques_dict[ques][0]
                        fw.write('----'.join([ques, answer]) + '\n')
                    else:
                        print(ques)



if __name__ == '__main__':
    generate_test(r'E:\intelligent_q&a\ipeg_data\ques.txt', r'E:\intelligent_q&a\ipeg_data\simility_ques', r'E:\intelligent_q&a\ipeg_data\test')
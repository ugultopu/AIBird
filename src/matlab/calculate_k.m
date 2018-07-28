data=csvread(evalin('base', 'FILE_NAME'),1,1);
max_k=5;
k_means_result=zeros(1,max_k);
for i = 1: max_k
    [l,w]=size(data);
    if l<i
        break
    end
    [y,index,centroids]=Structure_prune(i);
    sil=silhouette(data,index);
    %disp(mean(sil));
    k_means_result(i)=mean(sil);
end
[M,I]=max(k_means_result);
